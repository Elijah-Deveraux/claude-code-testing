"""
PDF Summarization Streamlit Frontend.

This is the main Streamlit application for the PDF summarization system.
It provides a user-friendly interface for:
- Uploading PDF documents
- Viewing uploaded documents
- Generating summaries (brief and detailed)
- Displaying summaries with metadata
"""

import streamlit as st
import requests
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import time

# Page configuration
st.set_page_config(
    page_title="PDF Summarization System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-key-12345")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .document-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .summary-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-top: 1rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e8f4f8;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """
    Initialize Streamlit session state variables.

    Session state maintains data across reruns of the app.
    """
    if "documents" not in st.session_state:
        st.session_state.documents = []

    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None

    if "current_summary" not in st.session_state:
        st.session_state.current_summary = None

    if "upload_status" not in st.session_state:
        st.session_state.upload_status = None

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()


def check_backend_health() -> bool:
    """
    Check if the backend API is accessible.

    Returns:
        True if backend is healthy, False otherwise
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        return False


def get_api_headers() -> Dict[str, str]:
    """
    Get headers for API requests including authentication.

    Returns:
        Dictionary of headers
    """
    return {
        "X-API-Key": API_KEY
    }


def main():
    """Main application function."""

    # Initialize session state
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">📄 PDF Summarization System</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Upload PDFs and generate AI-powered summaries</div>',
        unsafe_allow_html=True
    )

    # Check backend health
    if not check_backend_health():
        st.error(
            "⚠️ Cannot connect to backend API. "
            "Please ensure the FastAPI server is running at "
            f"{API_BASE_URL}"
        )
        st.info(
            "Start the backend with: `uvicorn src.api.main:app --reload`"
        )
        st.stop()

    # Sidebar
    render_sidebar()

    # Main content area
    render_main_content()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "PDF Summarization System | Powered by LangChain & Google Gemini"
        "</div>",
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar with navigation and settings."""

    with st.sidebar:
        st.header("🗂️ Navigation")

        # Action selection
        action = st.radio(
            "Select Action",
            ["Upload PDF", "View Documents", "Generate Summary"],
            index=0
        )

        st.session_state.current_action = action

        st.markdown("---")

        # Document list section
        st.header("📚 Documents")

        # Refresh button
        if st.button("🔄 Refresh List", use_container_width=True):
            load_documents()
            st.session_state.last_refresh = time.time()

        # Display document list
        if st.session_state.documents:
            st.caption(f"Total: {len(st.session_state.documents)} documents")

            # Create selectbox for documents
            doc_options = [
                f"{doc['filename']} ({doc['num_pages']} pages)"
                for doc in st.session_state.documents
            ]

            selected_idx = st.selectbox(
                "Select Document",
                range(len(doc_options)),
                format_func=lambda i: doc_options[i],
                key="doc_selector"
            )

            if selected_idx is not None:
                st.session_state.selected_document = st.session_state.documents[selected_idx]
        else:
            st.info("No documents uploaded yet")

        st.markdown("---")

        # Settings section
        with st.expander("⚙️ Settings"):
            st.caption(f"API URL: {API_BASE_URL}")
            st.caption(f"Last refresh: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_refresh))}")


def render_main_content():
    """Render the main content area based on selected action."""

    action = st.session_state.get("current_action", "Upload PDF")

    if action == "Upload PDF":
        render_upload_section()
    elif action == "View Documents":
        render_documents_section()
    elif action == "Generate Summary":
        render_summary_section()


def render_upload_section():
    """Render the PDF upload section."""

    st.header("📤 Upload PDF Document")

    st.write(
        "Upload a PDF document to add it to the system. "
        "The document will be processed, chunked, and stored for summarization."
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Select a PDF file to upload (max 200MB)",
        key="pdf_uploader"
    )

    if uploaded_file is not None:
        # Try to read the file immediately when it's uploaded
        try:
            # Read file bytes directly
            file_bytes = uploaded_file.read()

            # Display file info
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Filename", uploaded_file.name)
            with col2:
                file_size_mb = len(file_bytes) / (1024 * 1024)
                st.metric("Size", f"{file_size_mb:.2f} MB")
            with col3:
                st.metric("Type", uploaded_file.type)

            # Upload button
            if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
                with st.spinner("Uploading and processing..."):
                    upload_pdf_from_bytes(uploaded_file.name, file_bytes)

        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("💡 If you see a session error, try refreshing the page or using a different browser.")


def render_documents_section():
    """Render the documents viewing section."""

    st.header("📚 Document Library")

    if not st.session_state.documents:
        st.info("No documents available. Upload a PDF to get started!")
        load_documents()
        return

    st.write(f"Showing {len(st.session_state.documents)} document(s)")

    # Display documents in a grid
    for doc in st.session_state.documents:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.markdown(f"**{doc['filename']}**")
            with col2:
                st.text(f"📄 {doc['num_pages']} pages")
            with col3:
                # num_chunks may not be in the list response, use default
                num_chunks = doc.get('num_chunks', '—')
                st.text(f"📦 {num_chunks} chunks")
            with col4:
                if st.button("🗑️", key=f"delete_{doc['document_id']}"):
                    delete_document(doc['document_id'])

            st.caption(f"ID: {doc['document_id']}")
            st.markdown("---")


def render_summary_section():
    """Render the summary generation section."""

    st.header("✨ Generate Summary")

    if not st.session_state.selected_document:
        st.warning("Please select a document from the sidebar first!")
        return

    doc = st.session_state.selected_document

    # Display selected document info
    st.markdown(f"### Selected Document: {doc['filename']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pages", doc.get('num_pages', 'N/A'))
    with col2:
        # num_chunks may not be in the list response
        st.metric("Chunks", doc.get('num_chunks', 'N/A'))
    with col3:
        status = doc.get('status', 'unknown')
        status_color = "🟢" if status == 'completed' else "🟡"
        st.metric("Status", f"{status_color} {status}")

    st.markdown("---")

    # Summary type selection
    st.subheader("Summary Type")
    summary_type = st.radio(
        "Choose summary length:",
        ["Brief", "Detailed"],
        horizontal=True,
        help="Brief: 3-5 sentences | Detailed: 300-500 words"
    )

    # Generate button
    if st.button("✨ Generate Summary", type="primary", use_container_width=True):
        generate_summary(doc['document_id'], summary_type.lower())

    # Display summary if available
    if st.session_state.current_summary:
        display_summary(st.session_state.current_summary)


def display_summary(summary_data: Dict[str, Any]):
    """
    Display the generated summary with metadata.

    Args:
        summary_data: Summary response from backend
    """
    st.markdown("---")
    st.subheader("📝 Generated Summary")

    # Summary metadata
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Type", summary_data.get('summary_type', 'N/A').title())
    with col2:
        st.metric("Tokens Used", summary_data.get('tokens_used', 0))
    with col3:
        pages = summary_data.get('page_references', [])
        page_str = f"Pages {min(pages)}-{max(pages)}" if pages else "N/A"
        st.metric("Source", page_str)
    with col4:
        cached = summary_data.get('cached', False)
        cache_icon = "💾" if cached else "🆕"
        st.metric("Cache", f"{cache_icon} {'Hit' if cached else 'Miss'}")

    # Summary text
    st.markdown('<div class="summary-box">', unsafe_allow_html=True)
    st.markdown(summary_data.get('summary_text', 'No summary available'))
    st.markdown('</div>', unsafe_allow_html=True)

    # Timestamp
    st.caption(f"Generated at: {summary_data.get('timestamp', 'N/A')}")


# Backend API functions
def load_documents():
    """Load documents from the backend API."""
    try:
        with st.spinner("Loading documents..."):
            response = requests.get(
                f"{API_BASE_URL}/documents",
                headers=get_api_headers(),
                timeout=10
            )

            if response.status_code == 200:
                st.session_state.documents = response.json().get('documents', [])
            else:
                st.error(f"Failed to load documents: {response.status_code}")

    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")


def upload_pdf_from_bytes(file_name: str, file_bytes: bytes):
    """
    Upload a PDF file to the backend using file bytes.

    Args:
        file_name: Name of the file
        file_bytes: File content as bytes
    """
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Uploading file...")
        progress_bar.progress(20)

        # Prepare file for upload - Create a file-like object from bytes
        import io
        file_obj = io.BytesIO(file_bytes)

        # Prepare multipart form data
        files = {
            'file': (file_name, file_obj, 'application/pdf')
        }

        # Get headers - Do NOT set Content-Type, let requests handle it for multipart
        headers = get_api_headers()

        # Upload to backend
        response = requests.post(
            f"{API_BASE_URL}/documents/upload-pdf",
            headers=headers,
            files=files,
            timeout=120
        )

        progress_bar.progress(60)
        status_text.text("Processing document...")

        if response.status_code == 201:
            result = response.json()
            progress_bar.progress(100)
            status_text.text("Upload complete!")

            st.success(
                f"✅ Successfully uploaded and processed **{file_name}**!\n\n"
                f"- Document ID: {result.get('document_id', 'N/A')}\n"
                f"- Pages: {result.get('num_pages', 0)}\n"
                f"- Chunks: {result.get('num_chunks', 0)}"
            )

            # Refresh document list
            time.sleep(1)
            load_documents()

        else:
            progress_bar.empty()
            status_text.empty()
            try:
                error_response = response.json()
                error_msg = error_response.get('error', error_response.get('detail', 'Unknown error'))
            except:
                error_msg = response.text
            st.error(f"❌ Upload failed (Status {response.status_code}): {error_msg}")

    except Exception as e:
        st.error(f"❌ Error during upload: {str(e)}")
        st.info("💡 Try refreshing the page and uploading again.")


def generate_summary(document_id: str, summary_type: str):
    """
    Generate a summary for a document.

    Args:
        document_id: ID of the document
        summary_type: Type of summary ('brief' or 'detailed')
    """
    try:
        with st.spinner(f"Generating {summary_type} summary... This may take a moment."):
            response = requests.post(
                f"{API_BASE_URL}/summarize",
                headers=get_api_headers(),
                json={
                    "document_id": document_id,
                    "summary_type": summary_type
                },
                timeout=60
            )

            if response.status_code == 200:
                summary_data = response.json()
                st.session_state.current_summary = summary_data

                cached = summary_data.get('cached', False)
                if cached:
                    st.info("💾 Retrieved from cache")
                else:
                    st.success("✅ Summary generated successfully!")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Failed to generate summary: {error_detail}")

    except Exception as e:
        st.error(f"❌ Error generating summary: {str(e)}")


def delete_document(document_id: str):
    """
    Delete a document from the system.

    Args:
        document_id: ID of the document to delete
    """
    try:
        with st.spinner("Deleting document..."):
            response = requests.delete(
                f"{API_BASE_URL}/documents/{document_id}",
                headers=get_api_headers(),
                timeout=10
            )

            if response.status_code == 200:
                st.success("✅ Document deleted successfully!")
                load_documents()
                st.session_state.selected_document = None
                st.rerun()
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Failed to delete document: {error_detail}")

    except Exception as e:
        st.error(f"❌ Error deleting document: {str(e)}")


if __name__ == "__main__":
    # Load documents on startup
    if not st.session_state.get("documents"):
        load_documents()

    # Run main app
    main()

