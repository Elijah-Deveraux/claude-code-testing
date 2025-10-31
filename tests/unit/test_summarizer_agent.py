"""
Unit tests for SummarizerAgent.

Tests cover:
- Summary generation
- Token tracking
- Caching
- Validation
- Context management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.agents.summarizer_agent import (
    SummarizerAgent,
    SummaryType,
    SummaryRequest,
    SummaryResponse,
    TokenUsage
)


class TestSummarizerAgentInitialization:
    """Test SummarizerAgent initialization."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_init_with_gemini(self, mock_gemini):
        """Test initialization with Gemini provider."""
        mock_retrieval = Mock()

        agent = SummarizerAgent(
            llm_provider="gemini",
            model_name="gemini-1.5-flash",
            retrieval_agent=mock_retrieval,
            google_api_key="test-key"
        )

        assert agent.llm_provider == "gemini"
        assert agent.model_name == "gemini-1.5-flash"
        assert agent.llm is not None
        assert agent.brief_chain is not None
        assert agent.detailed_chain is not None

    @patch('src.agents.summarizer_agent.Ollama')
    def test_init_with_ollama(self, mock_ollama):
        """Test initialization with Ollama provider."""
        mock_retrieval = Mock()

        agent = SummarizerAgent(
            llm_provider="ollama",
            model_name="llama3.2",
            retrieval_agent=mock_retrieval
        )

        assert agent.llm_provider == "ollama"
        assert agent.model_name == "llama3.2"
        assert agent.llm is not None

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_init_without_api_key_raises_error(self, mock_gemini, monkeypatch):
        """Test initialization without API key raises ValueError."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            SummarizerAgent(
                llm_provider="gemini",
                google_api_key=None
            )

    def test_init_with_invalid_provider_raises_error(self):
        """Test initialization with invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            SummarizerAgent(llm_provider="invalid")


class TestTokenCounting:
    """Test token counting functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_count_tokens_with_tiktoken(self, mock_gemini):
        """Test token counting using tiktoken."""
        agent = SummarizerAgent(google_api_key="test-key")

        text = "This is a test sentence."
        token_count = agent._count_tokens(text)

        assert isinstance(token_count, int)
        assert token_count > 0

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_count_tokens_fallback(self, mock_gemini):
        """Test token counting fallback approximation."""
        agent = SummarizerAgent(google_api_key="test-key")
        agent.tokenizer = None  # Force fallback

        text = "This is a test."  # 16 characters
        token_count = agent._count_tokens(text)

        # Fallback: 1 token = 4 characters
        assert token_count == 16 // 4


class TestSummaryValidation:
    """Test summary validation functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_validate_brief_summary_success(self, mock_gemini):
        """Test validation of valid brief summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        summary = "This is sentence one. This is sentence two. This is sentence three."
        is_valid = agent._validate_summary(summary, SummaryType.BRIEF)

        assert is_valid is True

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_validate_brief_summary_too_short(self, mock_gemini):
        """Test validation fails for too short brief summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        summary = "One sentence."
        is_valid = agent._validate_summary(summary, SummaryType.BRIEF)

        assert is_valid is False

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_validate_detailed_summary_success(self, mock_gemini):
        """Test validation of valid detailed summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        # Create a 400-word summary
        summary = " ".join(["word"] * 400)
        is_valid = agent._validate_summary(summary, SummaryType.DETAILED)

        assert is_valid is True

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_validate_detailed_summary_too_short(self, mock_gemini):
        """Test validation fails for too short detailed summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        summary = " ".join(["word"] * 100)  # Only 100 words
        is_valid = agent._validate_summary(summary, SummaryType.DETAILED)

        assert is_valid is False

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_validate_empty_summary(self, mock_gemini):
        """Test validation fails for empty summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        is_valid = agent._validate_summary("", SummaryType.BRIEF)

        assert is_valid is False


class TestContextRetrieval:
    """Test context retrieval functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_retrieve_context_success(self, mock_gemini, mock_retrieval_agent):
        """Test successful context retrieval."""
        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=mock_retrieval_agent
        )

        context = agent._retrieve_context("test-doc-123")

        assert len(context) > 0
        assert all("content" in chunk for chunk in context)
        mock_retrieval_agent.search.assert_called_once()

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_retrieve_context_without_agent_raises_error(self, mock_gemini):
        """Test context retrieval without retrieval agent raises error."""
        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=None
        )

        with pytest.raises(ValueError, match="Retrieval agent not configured"):
            agent._retrieve_context("test-doc-123")

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_retrieve_context_with_query(self, mock_gemini, mock_retrieval_agent):
        """Test context retrieval with specific query."""
        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=mock_retrieval_agent
        )

        context = agent._retrieve_context("test-doc-123", query="specific topic")

        mock_retrieval_agent.search.assert_called_once()
        call_args = mock_retrieval_agent.search.call_args
        assert call_args[1]["query"] == "specific topic"


class TestPageReferenceExtraction:
    """Test page reference extraction."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_extract_page_references(self, mock_gemini):
        """Test extracting page numbers from context."""
        agent = SummarizerAgent(google_api_key="test-key")

        context = [
            {"page_number": 1},
            {"page_number": 3},
            {"page_number": 1},  # Duplicate
            {"page_number": 5}
        ]

        pages = agent._extract_page_references(context)

        assert pages == [1, 3, 5]  # Sorted, unique

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_extract_page_references_empty(self, mock_gemini):
        """Test extracting from empty context."""
        agent = SummarizerAgent(google_api_key="test-key")

        pages = agent._extract_page_references([])

        assert pages == []


class TestTokenTracking:
    """Test token tracking functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_track_token_usage(self, mock_gemini, cleanup_test_files):
        """Test token usage tracking."""
        agent = SummarizerAgent(google_api_key="test-key")

        usage = TokenUsage(
            summary_id="test-summary",
            document_id="test-doc",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            timestamp=datetime.now()
        )

        agent._track_token_usage(usage)

        assert len(agent.token_log) == 1
        assert agent.token_log[0].total_tokens == 150

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_get_token_statistics(self, mock_gemini):
        """Test getting token statistics."""
        agent = SummarizerAgent(google_api_key="test-key")

        # Add some usage data
        for i in range(3):
            usage = TokenUsage(
                summary_id=f"summary-{i}",
                document_id="test-doc",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                timestamp=datetime.now()
            )
            agent.token_log.append(usage)

        stats = agent.get_token_statistics()

        assert stats["total_tokens"] == 450
        assert stats["summary_count"] == 3
        assert stats["average_tokens_per_summary"] == 150

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_get_token_statistics_filtered(self, mock_gemini):
        """Test getting token statistics filtered by document."""
        agent = SummarizerAgent(google_api_key="test-key")

        # Add usage for different documents
        agent.token_log.append(TokenUsage(
            summary_id="s1", document_id="doc1",
            prompt_tokens=100, completion_tokens=50,
            total_tokens=150, timestamp=datetime.now()
        ))
        agent.token_log.append(TokenUsage(
            summary_id="s2", document_id="doc2",
            prompt_tokens=200, completion_tokens=100,
            total_tokens=300, timestamp=datetime.now()
        ))

        stats = agent.get_token_statistics(document_id="doc1")

        assert stats["total_tokens"] == 150
        assert stats["summary_count"] == 1


class TestSummaryCaching:
    """Test summary caching functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_cache_summary(self, mock_gemini):
        """Test caching a summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        response = SummaryResponse(
            summary_id="test-summary",
            document_id="test-doc",
            summary_text="Test summary",
            summary_type=SummaryType.BRIEF,
            tokens_used=50,
            page_references=[1, 2],
            timestamp=datetime.now()
        )

        agent._cache_summary(response)

        cache_key = "test-doc_brief"
        assert cache_key in agent.summary_cache
        assert agent.summary_cache[cache_key].summary_id == "test-summary"

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_check_cache_hit(self, mock_gemini):
        """Test cache hit returns cached summary."""
        agent = SummarizerAgent(google_api_key="test-key")

        response = SummaryResponse(
            summary_id="test-summary",
            document_id="test-doc",
            summary_text="Test summary",
            summary_type=SummaryType.BRIEF,
            tokens_used=50,
            page_references=[1, 2],
            timestamp=datetime.now(),
            cached=False
        )

        agent._cache_summary(response)

        cached = agent._check_cache("test-doc", SummaryType.BRIEF)

        assert cached is not None
        assert cached.cached is True
        assert cached.summary_id == "test-summary"

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_check_cache_miss(self, mock_gemini):
        """Test cache miss returns None."""
        agent = SummarizerAgent(google_api_key="test-key")

        cached = agent._check_cache("non-existent-doc", SummaryType.BRIEF)

        assert cached is None


class TestSummaryGeneration:
    """Test summary generation functionality."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    @patch('src.agents.summarizer_agent.LLMChain')
    def test_generate_summary_brief(self, mock_chain_class, mock_gemini, mock_retrieval_agent):
        """Test generating brief summary."""
        # Setup mocks
        mock_chain = Mock()
        mock_chain.run.return_value = "This is a brief summary. It has three sentences. Testing complete."
        mock_chain_class.return_value = mock_chain

        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=mock_retrieval_agent
        )
        agent.brief_chain = mock_chain

        request = SummaryRequest(
            document_id="test-doc",
            summary_type=SummaryType.BRIEF
        )

        response = agent.generate_summary(request)

        assert response.summary_type == SummaryType.BRIEF
        assert response.cached is False
        assert response.tokens_used > 0
        assert len(agent.token_log) == 1

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_generate_summary_uses_cache(self, mock_gemini, mock_retrieval_agent):
        """Test that generate_summary uses cached results."""
        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=mock_retrieval_agent
        )

        # Pre-cache a summary
        cached_response = SummaryResponse(
            summary_id="cached-summary",
            document_id="test-doc",
            summary_text="Cached summary",
            summary_type=SummaryType.BRIEF,
            tokens_used=50,
            page_references=[1],
            timestamp=datetime.now()
        )
        agent._cache_summary(cached_response)

        request = SummaryRequest(
            document_id="test-doc",
            summary_type=SummaryType.BRIEF
        )

        response = agent.generate_summary(request)

        assert response.cached is True
        assert response.summary_id == "cached-summary"
        # Should not call retrieval agent since using cache
        mock_retrieval_agent.search.assert_not_called()


class TestAsyncSummaryGeneration:
    """Test async summary generation."""

    @pytest.mark.asyncio
    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    async def test_generate_summary_async(self, mock_gemini, mock_retrieval_agent):
        """Test async summary generation."""
        agent = SummarizerAgent(
            google_api_key="test-key",
            retrieval_agent=mock_retrieval_agent
        )

        # Pre-cache to avoid actual LLM call
        cached_response = SummaryResponse(
            summary_id="test",
            document_id="test-doc",
            summary_text="Test",
            summary_type=SummaryType.BRIEF,
            tokens_used=10,
            page_references=[],
            timestamp=datetime.now()
        )
        agent._cache_summary(cached_response)

        request = SummaryRequest(
            document_id="test-doc",
            summary_type=SummaryType.BRIEF
        )

        response = await agent.generate_summary_async(request)

        assert response is not None
        assert isinstance(response, SummaryResponse)


class TestContextWindowManagement:
    """Test context window management."""

    @patch('src.agents.summarizer_agent.ChatGoogleGenerativeAI')
    def test_context_truncation_when_over_limit(self, mock_gemini, mock_retrieval_agent):
        """Test that context is truncated when over token limit."""
        # This would require actual implementation testing
        # Placeholder for context management validation
        pass

