"""
Summarizer Agent for generating PDF summaries using LLM.

This agent is responsible for:
1. Retrieving relevant context from the Retrieval Agent
2. Formatting prompts for the LLM using LangChain PromptTemplates
3. Generating summaries (brief and detailed) via LangChain LLM chains
4. Tracking token usage
5. Caching summaries for performance

This agent uses LangChain framework for:
- LLM integration (Google Gemini or Ollama via LangChain)
- Prompt templates (PromptTemplate, ChatPromptTemplate)
- Chains (LLMChain for structured LLM interactions)
- Callbacks (for token tracking and monitoring)
"""

import logging
import os
import uuid
import tiktoken
import json
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path

# LangChain imports for LLM operations
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.schema import BaseLanguageModel

logger = logging.getLogger(__name__)


class SummaryType(Enum):
    """Enumeration of available summary types."""
    BRIEF = "brief"
    DETAILED = "detailed"


@dataclass
class SummaryRequest:
    """
    Request parameters for generating a summary.

    Attributes:
        document_id: ID of the document to summarize
        summary_type: Type of summary (brief or detailed)
        query: Optional specific query/focus for the summary
        max_tokens: Maximum tokens for the response
    """
    document_id: str
    summary_type: SummaryType
    query: Optional[str] = None
    max_tokens: int = 4000


@dataclass
class SummaryResponse:
    """
    Response containing the generated summary.

    Attributes:
        summary_id: Unique identifier for this summary
        document_id: ID of the source document
        summary_text: The generated summary text
        summary_type: Type of summary generated
        tokens_used: Number of tokens consumed
        page_references: List of page numbers referenced
        timestamp: When the summary was generated
        cached: Whether this was retrieved from cache
    """
    summary_id: str
    document_id: str
    summary_text: str
    summary_type: SummaryType
    tokens_used: int
    page_references: List[int]
    timestamp: datetime
    cached: bool = False


@dataclass
class TokenUsage:
    """
    Token usage statistics for a summary generation.

    Attributes:
        summary_id: ID of the summary
        document_id: ID of the document
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used
        timestamp: When the tokens were used
    """
    summary_id: str
    document_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: datetime


class SummarizerAgent:
    """
    Agent responsible for generating summaries of PDF documents.

    This agent uses an LLM (Google Gemini or Ollama) to generate summaries
    based on relevant context retrieved from the Retrieval Agent. It supports
    two summary modes:
    - Brief: 3-5 concise sentences
    - Detailed: 300-500 word comprehensive summary

    The agent includes token tracking, caching, and context management.

    Attributes:
        llm_provider: LLM provider to use ("gemini" or "ollama")
        model_name: Name of the specific model
        max_context_tokens: Maximum tokens for context window
        retrieval_agent: Instance of RetrievalAgent for context retrieval
    """

    def __init__(
        self,
        llm_provider: Literal["gemini", "ollama"] = "gemini",
        model_name: str = "gemini-1.5-flash",
        max_context_tokens: int = 4000,
        retrieval_agent: Optional[Any] = None,
        google_api_key: Optional[str] = None
    ) -> None:
        """
        Initialize the Summarizer Agent with LangChain LLM components.

        Args:
            llm_provider: LLM provider ("gemini" or "ollama")
            model_name: Specific model to use
            max_context_tokens: Maximum tokens for context
            retrieval_agent: Instance of RetrievalAgent
            google_api_key: Google API key for Gemini (uses env var if not provided)

        Raises:
            ValueError: If configuration is invalid
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.max_context_tokens = max_context_tokens
        self.retrieval_agent = retrieval_agent

        # Initialize LLM based on provider
        if llm_provider == "gemini":
            api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "GOOGLE_API_KEY must be provided or set in environment"
                )
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.3,  # Lower temperature for more focused summaries
                convert_system_message_to_human=True
            )
        elif llm_provider == "ollama":
            self.llm = Ollama(
                model=model_name,
                temperature=0.3
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        # Create prompt templates
        self.brief_prompt = PromptTemplate(
            input_variables=["context", "document_info"],
            template="""You are a professional document summarizer.
Generate a BRIEF summary (3-5 sentences) of the following document content.

Document Information:
{document_info}

Content:
{context}

Instructions:
- Write exactly 3-5 sentences
- Be concise and focus on the main points
- Use clear, professional language
- Include key findings or conclusions

Brief Summary:"""
        )

        self.detailed_prompt = PromptTemplate(
            input_variables=["context", "document_info"],
            template="""You are a professional document summarizer.
Generate a DETAILED summary (300-500 words) of the following document content.

Document Information:
{document_info}

Content:
{context}

Instructions:
- Write 300-500 words
- Cover all major topics and themes
- Include important details, findings, and conclusions
- Organize logically with clear structure
- Use professional language
- Maintain objectivity

Detailed Summary:"""
        )

        # Create LangChain chains
        self.brief_chain = LLMChain(llm=self.llm, prompt=self.brief_prompt)
        self.detailed_chain = LLMChain(llm=self.llm, prompt=self.detailed_prompt)

        # Initialize caching structures
        self.summary_cache: Dict[str, SummaryResponse] = {}
        self.token_log: List[TokenUsage] = []

        # Token counter
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoder: {e}. Using approximation.")
            self.tokenizer = None

        # Create logs directory for token tracking
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.token_log_file = self.logs_dir / "token_usage.jsonl"

        logger.info(
            f"SummarizerAgent initialized with LangChain: "
            f"provider={llm_provider}, model={model_name}"
        )

    def generate_summary(
        self,
        request: SummaryRequest
    ) -> SummaryResponse:
        """
        Generate a summary for a document.

        This is the main entry point for summary generation. It:
        1. Checks cache for existing summary
        2. Retrieves relevant context from Retrieval Agent
        3. Formats the prompt based on summary type
        4. Calls the LLM to generate summary
        5. Validates and formats the response
        6. Tracks token usage
        7. Caches the result

        Args:
            request: Summary request parameters

        Returns:
            SummaryResponse with the generated summary

        Raises:
            ValueError: If document_id is invalid
            Exception: If summary generation fails

        Example:
            >>> agent = SummarizerAgent()
            >>> request = SummaryRequest(
            ...     document_id="doc123",
            ...     summary_type=SummaryType.BRIEF
            ... )
            >>> response = agent.generate_summary(request)
            >>> print(response.summary_text)
        """
        logger.info(
            f"Generating {request.summary_type.value} summary for "
            f"document {request.document_id}"
        )

        try:
            # Step 1: Check cache
            cached_summary = self._check_cache(
                request.document_id,
                request.summary_type
            )
            if cached_summary:
                logger.info("Returning cached summary")
                return cached_summary

            # Step 2: Retrieve context
            context_chunks = self._retrieve_context(
                request.document_id,
                request.query
            )

            if not context_chunks:
                raise ValueError(f"No context found for document {request.document_id}")

            # Step 3: Get document info
            doc_info = self.retrieval_agent.get_document_info(request.document_id)
            if not doc_info:
                raise ValueError(f"Document {request.document_id} not found")

            # Step 4: Prepare context text
            context_text = "\n\n---\n\n".join([
                f"[Chunk {chunk['chunk_index']}]\n{chunk['content']}"
                for chunk in context_chunks
            ])

            # Ensure context doesn't exceed token limit
            context_tokens = self._count_tokens(context_text)
            if context_tokens > self.max_context_tokens:
                logger.warning(
                    f"Context too large ({context_tokens} tokens), truncating"
                )
                # Truncate context (simple approach: remove last chunks)
                while context_tokens > self.max_context_tokens and context_chunks:
                    context_chunks.pop()
                    context_text = "\n\n---\n\n".join([
                        f"[Chunk {chunk['chunk_index']}]\n{chunk['content']}"
                        for chunk in context_chunks
                    ])
                    context_tokens = self._count_tokens(context_text)

            # Step 5: Format document info
            doc_info_text = f"Filename: {doc_info['filename']}\nPages: {doc_info['num_pages']}"

            # Step 6: Generate summary using LangChain
            if request.summary_type == SummaryType.BRIEF:
                chain = self.brief_chain
            else:
                chain = self.detailed_chain

            summary_text = chain.run(
                context=context_text,
                document_info=doc_info_text
            ).strip()

            # Step 7: Validate summary
            is_valid = self._validate_summary(summary_text, request.summary_type)
            if not is_valid:
                logger.warning("Generated summary did not pass validation")

            # Step 8: Extract page references
            page_refs = self._extract_page_references(context_chunks)

            # Step 9: Track token usage
            prompt_tokens = self._count_tokens(context_text + doc_info_text)
            completion_tokens = self._count_tokens(summary_text)
            total_tokens = prompt_tokens + completion_tokens

            summary_id = str(uuid.uuid4())

            usage = TokenUsage(
                summary_id=summary_id,
                document_id=request.document_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                timestamp=datetime.now()
            )
            self._track_token_usage(usage)

            # Step 10: Create response
            response = SummaryResponse(
                summary_id=summary_id,
                document_id=request.document_id,
                summary_text=summary_text,
                summary_type=request.summary_type,
                tokens_used=total_tokens,
                page_references=page_refs,
                timestamp=datetime.now(),
                cached=False
            )

            # Step 11: Cache summary
            self._cache_summary(response)

            logger.info(
                f"Successfully generated {request.summary_type.value} summary "
                f"({total_tokens} tokens)"
            )

            return response

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise

    def _check_cache(
        self,
        document_id: str,
        summary_type: SummaryType
    ) -> Optional[SummaryResponse]:
        """
        Check if a cached summary exists for the document.

        Args:
            document_id: ID of the document
            summary_type: Type of summary

        Returns:
            Cached SummaryResponse if found, None otherwise
        """
        logger.debug(f"Checking cache for document {document_id}")

        cache_key = f"{document_id}_{summary_type.value}"
        if cache_key in self.summary_cache:
            logger.info(f"Cache hit for document {document_id}")
            cached_response = self.summary_cache[cache_key]
            # Mark as cached
            cached_response.cached = True
            return cached_response

        return None

    def _retrieve_context(
        self,
        document_id: str,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for summary generation.

        Args:
            document_id: ID of the document
            query: Optional specific query to focus retrieval

        Returns:
            List of relevant document chunks with metadata

        Raises:
            Exception: If retrieval fails
        """
        logger.debug(f"Retrieving context for document {document_id}")

        if not self.retrieval_agent:
            raise ValueError("Retrieval agent not configured")

        try:
            # If query provided, use it for focused retrieval
            # Otherwise, use a generic query to get document overview
            search_query = query or "Provide an overview of the main content"

            # Get top 5 relevant chunks
            search_results = self.retrieval_agent.search(
                query=search_query,
                document_id=document_id,
                top_k=5
            )

            # Convert search results to context format
            context_chunks = []
            for result in search_results:
                context_chunks.append({
                    "content": result.chunk.content,
                    "page_number": result.chunk.page_number,
                    "chunk_index": result.chunk.chunk_index,
                    "score": result.score,
                    "metadata": result.chunk.metadata
                })

            logger.info(f"Retrieved {len(context_chunks)} context chunks")
            return context_chunks

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise

    def _format_prompt(
        self,
        context: List[Dict[str, Any]],
        summary_type: SummaryType,
        query: Optional[str] = None
    ) -> str:
        """
        Format the prompt for the LLM based on context and summary type.

        Args:
            context: List of context chunks
            summary_type: Type of summary to generate
            query: Optional specific query

        Returns:
            Formatted prompt string

        Example:
            Brief prompt: "Summarize the following in 3-5 sentences: {context}"
            Detailed prompt: "Provide a detailed 300-500 word summary: {context}"
        """
        logger.debug(f"Formatting {summary_type.value} prompt")
        # TODO: Implement prompt formatting in Stage 4
        raise NotImplementedError("Prompt formatting will be implemented in Stage 4")

    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM to generate the summary.

        Uses LangChain's LLMChain for structured LLM interaction.
        Handles both Gemini and Ollama providers.

        Args:
            prompt: Formatted prompt for the LLM

        Returns:
            Generated summary text

        Raises:
            Exception: If LLM call fails
        """
        logger.debug("Calling LLM for summary generation")
        # TODO: Implement LLM call using LangChain in Stage 4
        raise NotImplementedError("LLM call will be implemented in Stage 4")

    def _validate_summary(
        self,
        summary: str,
        summary_type: SummaryType
    ) -> bool:
        """
        Validate that the summary meets the requirements.

        Brief: Should have 3-5 sentences
        Detailed: Should have 300-500 words

        Args:
            summary: Generated summary text
            summary_type: Expected summary type

        Returns:
            True if valid, False otherwise
        """
        logger.debug("Validating summary")

        if not summary or not summary.strip():
            logger.warning("Summary is empty")
            return False

        if summary_type == SummaryType.BRIEF:
            # Count sentences (approximate by counting periods, exclamation marks, question marks)
            sentence_endings = summary.count('.') + summary.count('!') + summary.count('?')
            if sentence_endings < 3 or sentence_endings > 5:
                logger.warning(
                    f"Brief summary has {sentence_endings} sentences, expected 3-5"
                )
                return False

        elif summary_type == SummaryType.DETAILED:
            # Count words
            word_count = len(summary.split())
            if word_count < 300 or word_count > 500:
                logger.warning(
                    f"Detailed summary has {word_count} words, expected 300-500"
                )
                return False

        return True

    def _extract_page_references(
        self,
        context: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Extract page numbers from the context chunks.

        Args:
            context: List of context chunks with metadata

        Returns:
            Sorted list of unique page numbers
        """
        logger.debug("Extracting page references")

        page_numbers = set()
        for chunk in context:
            page_num = chunk.get("page_number", 0)
            if page_num > 0:
                page_numbers.add(page_num)

        return sorted(list(page_numbers))

    def _count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Uses tiktoken for accurate token counting.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting error: {e}. Using approximation.")

        # Fallback: approximate 1 token = 4 characters
        return len(text) // 4

    def _track_token_usage(self, usage: TokenUsage) -> None:
        """
        Track token usage for a summary generation.

        Logs usage to file and stores in database.

        Args:
            usage: Token usage statistics
        """
        logger.info(
            f"Token usage - Summary: {usage.summary_id}, "
            f"Total tokens: {usage.total_tokens}"
        )

        # Add to in-memory log
        self.token_log.append(usage)

        # Log to file
        try:
            with open(self.token_log_file, 'a') as f:
                log_entry = {
                    "summary_id": usage.summary_id,
                    "document_id": usage.document_id,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "timestamp": usage.timestamp.isoformat()
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging token usage to file: {e}")

    def _cache_summary(self, response: SummaryResponse) -> None:
        """
        Cache the generated summary for future use.

        Args:
            response: Summary response to cache
        """
        logger.debug(f"Caching summary {response.summary_id}")

        cache_key = f"{response.document_id}_{response.summary_type.value}"
        self.summary_cache[cache_key] = response

        logger.info(f"Cached summary for document {response.document_id}")

    def get_token_statistics(
        self,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Args:
            document_id: Optional filter by document ID

        Returns:
            Dictionary with token usage statistics

        Example:
            >>> agent = SummarizerAgent()
            >>> stats = agent.get_token_statistics()
            >>> print(f"Total tokens used: {stats['total_tokens']}")
        """
        logger.debug("Retrieving token statistics")

        # Filter by document_id if provided
        relevant_usage = self.token_log
        if document_id:
            relevant_usage = [
                u for u in self.token_log
                if u.document_id == document_id
            ]

        if not relevant_usage:
            return {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "summary_count": 0
            }

        total_tokens = sum(u.total_tokens for u in relevant_usage)
        prompt_tokens = sum(u.prompt_tokens for u in relevant_usage)
        completion_tokens = sum(u.completion_tokens for u in relevant_usage)

        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "summary_count": len(relevant_usage),
            "average_tokens_per_summary": total_tokens // len(relevant_usage) if relevant_usage else 0
        }

    async def generate_summary_async(
        self,
        request: SummaryRequest
    ) -> SummaryResponse:
        """
        Asynchronous version of generate_summary.

        Allows for non-blocking summary generation.

        Args:
            request: Summary request parameters

        Returns:
            SummaryResponse with the generated summary
        """
        logger.info(f"Async summary generation for document {request.document_id}")

        # For now, use a simple approach: run in executor
        # LangChain's async support can be added later if needed
        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.generate_summary,
            request
        )

        return response
