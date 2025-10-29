"""
RLVR Automation Demo - WhatsApp-Style UI with Explainability

A beautiful, modern WhatsApp-inspired interface for RAG-based PDF question answering
with full explainability, event tracing, and RAGAS scoring visualization.
"""

import streamlit as st
from utils.api_client import get_api_client
import time
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="RLVR Automation Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def initialize_session_state():
    """Initialize session state variables."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "api_client" not in st.session_state:
        st.session_state.api_client = get_api_client()
    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "current_question" not in st.session_state:
        st.session_state.current_question = ""


def get_whatsapp_css():
    """Get WhatsApp-style CSS."""
    return """
    <style>
    /* Force light theme */
    :root {
        --bg-color: #f0f2f5;
        --chat-bg: #ffffff;
        --user-bubble: #d9fdd3;
        --bot-bubble: #ffffff;
        --text-color: #111b21;
        --secondary-text: #667781;
        --border-color: #e9edef;
        --header-bg: #008069;
        --header-text: #ffffff;
        --input-bg: #ffffff;
        --shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* CRITICAL: Remove ALL Streamlit default padding */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Remove gap at top and excessive padding */
    .main {
        padding-top: 0 !important;
    }

    section.main > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* Main container - light background */
    .stApp {
        background: #f0f2f5 !important;
    }

    /* Chat header */
    .chat-header {
        background: linear-gradient(135deg, #008069 0%, #00a884 100%);
        color: var(--header-text);
        padding: 1rem 1.5rem;
        border-radius: 8px 8px 0 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0;
        margin-top: 0.5rem;
    }

    /* Chat container - no min-height to avoid empty space */
    .chat-container {
        background-color: var(--chat-bg);
        border-radius: 0 0 8px 8px;
        padding: 1rem;
        max-height: 50vh;
        overflow-y: auto;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }

    /* Message bubbles - compact */
    .message-bubble {
        max-width: 75%;
        padding: 0.6rem 0.9rem;
        border-radius: 8px;
        margin-bottom: 0.4rem;
        word-wrap: break-word;
        box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    }

    .user-message {
        background-color: var(--user-bubble);
        margin-left: auto;
        border-radius: 8px 8px 0 8px;
    }

    .bot-message {
        background-color: var(--bot-bubble);
        margin-right: auto;
        border: 1px solid var(--border-color);
        border-radius: 8px 8px 8px 0;
    }

    .message-time {
        font-size: 0.7rem;
        color: var(--secondary-text);
        margin-top: 0.25rem;
        text-align: right;
    }

    /* Explainability section */
    .explain-section {
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin-top: 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }

    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .score-high {
        background-color: #d4edda;
        color: #155724;
    }

    .score-medium {
        background-color: #fff3cd;
        color: #856404;
    }

    .score-low {
        background-color: #f8d7da;
        color: #721c24;
    }

    /* Input area - compact */
    .input-container {
        background-color: var(--input-bg);
        padding: 0.75rem;
        border-radius: 8px;
        margin-top: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Upload section - compact */
    .upload-section {
        background-color: var(--chat-bg);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* API Links - compact */
    .api-links {
        background-color: var(--chat-bg);
        padding: 0.5rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .api-link {
        display: inline-block;
        padding: 0.3rem 0.7rem;
        margin: 0.2rem;
        background-color: #e3f2fd;
        color: #1976d2;
        text-decoration: none;
        border-radius: 4px;
        font-size: 0.75rem;
        transition: all 0.2s;
    }

    .api-link:hover {
        background-color: #1976d2;
        color: white;
        text-decoration: none;
    }

    .api-title {
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: #1976d2;
        font-size: 0.85rem;
    }

    /* Loading spinner - prominent and visible */
    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: white;
        border-radius: 8px;
        margin: 1rem auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        max-width: 400px;
    }

    .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #008069;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-text {
        font-size: 1.1rem;
        font-weight: 600;
        color: #008069;
        margin-bottom: 0.5rem;
    }

    .loading-subtext {
        font-size: 0.9rem;
        color: #667781;
        text-align: center;
    }
    </style>
    """


def render_chat_header():
    """Render WhatsApp-style chat header."""
    st.markdown("""
    <div class='chat-header'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div style='display: flex; align-items: center;'>
                <div style='font-size: 1.5rem; margin-right: 0.75rem;'>🤖</div>
                <div>
                    <div style='font-size: 1.25rem; font-weight: 600;'>RLVR Automation Demo</div>
                    <div style='font-size: 0.85rem; opacity: 0.9;'>Explainable AI Assistant</div>
                </div>
            </div>
            <div style='font-size: 0.85rem; opacity: 0.9;'>
                ✅ Online
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_score_badge(score, label):
    """Get HTML for score badge."""
    if score >= 0.7:
        badge_class = "score-high"
    elif score >= 0.4:
        badge_class = "score-medium"
    else:
        badge_class = "score-low"

    return f'<span class="score-badge {badge_class}">{label}: {score:.2f}</span>'


def render_explainability(chat_item):
    """Render explainability section - Simple for CEO, detailed for CTO."""
    # This function now returns None - we'll use Streamlit components instead
    return None


def render_message_bubble(message, is_user=True):
    """Render a WhatsApp-style message bubble."""
    bubble_class = "user-message" if is_user else "bot-message"
    icon = "👤" if is_user else "🤖"
    sender = "You" if is_user else "AI Assistant"

    timestamp = message.get('timestamp', datetime.now().strftime("%H:%M"))
    content = message.get('question' if is_user else 'answer', '')

    html = f"""
    <div style='display: flex; justify-content: {"flex-end" if is_user else "flex-start"}; margin-bottom: 1rem;'>
        <div class='message-bubble {bubble_class}'>
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <span style='margin-right: 0.5rem;'>{icon}</span>
                <strong style='font-size: 0.9rem;'>{sender}</strong>
            </div>
            <div style='margin-bottom: 0.25rem;'>{content}</div>
            <div class='message-time'>{timestamp}</div>
        </div>
    </div>
    """

    return html


def main():
    """Main application entry point."""
    # Initialize
    initialize_session_state()

    # Apply WhatsApp CSS
    st.markdown(get_whatsapp_css(), unsafe_allow_html=True)

    # Render header
    render_chat_header()

    # API Links section - compact
    st.markdown("""
    <div class='api-links'>
        <div class='api-title'>📚 API Docs</div>
        <a href='http://localhost:8000/docs' target='_blank' class='api-link'>Gateway</a>
        <a href='http://localhost:8001/docs' target='_blank' class='api-link'>QA</a>
        <a href='http://localhost:8002/docs' target='_blank' class='api-link'>Docs</a>
        <a href='http://localhost:8005/docs' target='_blank' class='api-link'>Training</a>
        <a href='http://localhost:8007/docs' target='_blank' class='api-link'>Ground Truth</a>
        <a href='http://localhost:15672' target='_blank' class='api-link'>RabbitMQ</a>
        <a href='http://localhost:6333/dashboard' target='_blank' class='api-link'>Qdrant</a>
    </div>
    """, unsafe_allow_html=True)

    # Upload section (compact button)
    col_upload1, col_upload2, col_upload3 = st.columns([1, 2, 1])
    with col_upload2:
        if st.button("📎 Upload PDF Document", use_container_width=True, disabled=st.session_state.processing):
            st.session_state.show_upload = not st.session_state.show_upload

    if st.session_state.show_upload:
        st.markdown("<div class='upload-section'>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF document to add to the knowledge base",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
            with col_btn2:
                if st.button("🚀 Process Document", type="primary", use_container_width=True):
                    with st.spinner("📄 Processing PDF..."):
                        try:
                            result = st.session_state.api_client.ingest_document(
                                file_bytes=uploaded_file.read(),
                                filename=uploaded_file.name
                            )
                            st.success(f"✅ Successfully processed {uploaded_file.name}!")
                            st.session_state.show_upload = False
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    # Chat container
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 1rem; color: #667781;'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🤖</div>
            <div style='font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem;'>
                Welcome to RLVR Automation Demo
            </div>
            <div style='font-size: 0.95rem;'>
                Ask questions about your documents and get explainable AI answers
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Render chat history
        for chat_item in st.session_state.chat_history:
            # User message
            st.markdown(render_message_bubble(chat_item, is_user=True), unsafe_allow_html=True)

            # Bot message
            st.markdown(render_message_bubble(chat_item, is_user=False), unsafe_allow_html=True)

            # Quality Score - Simple and clean
            verification = chat_item.get('verification')

            if verification:
                overall = verification.get('overall_score', 0)

                # Show quality score with color coding
                if overall >= 0.8:
                    quality_color = "#2e7d32"  # Green
                    quality_label = "Excellent"
                elif overall >= 0.6:
                    quality_color = "#f57c00"  # Orange
                    quality_label = "Good"
                else:
                    quality_color = "#d32f2f"  # Red
                    quality_label = "Fair"

                st.markdown(f"""
                <div style='margin: 0.5rem 0; padding: 0.75rem; background: #f8f9fa; border-radius: 6px; border-left: 3px solid {quality_color};'>
                    <div style='display: flex; align-items: center; gap: 0.5rem;'>
                        <span style='font-size: 0.9rem; color: #666;'>Answer Quality:</span>
                        <span style='font-weight: 600; color: {quality_color};'>{quality_label}</span>
                        <span style='font-size: 0.85rem; color: #999;'>({overall:.2f})</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Context sources (compact)
            if chat_item.get('contexts'):
                with st.expander(f"📚 View {len(chat_item['contexts'])} Context Sources", expanded=False):
                    for i, ctx in enumerate(chat_item['contexts'], 1):
                        st.markdown(f"**Source {i}:** Score: {ctx.get('score', 'N/A')}")
                        if 'metadata' in ctx:
                            meta = ctx['metadata']
                            st.caption(f"📄 {meta.get('source', 'N/A')} | Page {meta.get('page', 'N/A')}")
                        content = ctx.get('content', '')
                        st.text(content[:400] + "..." if len(content) > 400 else content)
                        if i < len(chat_item['contexts']):
                            st.divider()

    st.markdown("</div>", unsafe_allow_html=True)

    # Input area
    st.markdown("<div class='input-container'>", unsafe_allow_html=True)

    # Create form to enable Enter key submission
    with st.form(key="question_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            question = st.text_input(
                "Type your question...",
                placeholder="e.g., What are the pricing details? (Press Enter to send)",
                label_visibility="collapsed",
                key="question_input",
                disabled=st.session_state.processing
            )

        with col2:
            ask_button = st.form_submit_button(
                "📤 Send",
                use_container_width=True,
                type="primary",
                disabled=st.session_state.processing
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Show loading indicator if processing - PROMINENT AND VISIBLE
    if st.session_state.processing:
        st.markdown("""
        <div class='loading-spinner' style='position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 9999; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>
            <div class='spinner'></div>
            <div class='loading-text'>🤔 Thinking...</div>
            <div class='loading-subtext'>
                Searching through documents, analyzing context, and generating your answer...<br/>
                <strong>This may take 20-30 seconds on CPU</strong>
            </div>
        </div>
        <div style='position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.3); z-index: 9998;'></div>
        """, unsafe_allow_html=True)

    # Handle question submission
    if ask_button and question and not st.session_state.processing:
        # Set processing state
        st.session_state.processing = True
        st.session_state.current_question = question
        st.rerun()

    # Process the question if in processing state
    if st.session_state.processing and st.session_state.current_question:
        try:
            # Call API
            result = st.session_state.api_client.ask_question(
                question=st.session_state.current_question,
                collection_name="documents"
            )

            # Wait for verification to complete (with retry)
            event_id = result.get('metadata', {}).get('event_id')
            verification_data = None
            reward_data = None

            if event_id:
                # Try to get verification data with retries
                max_retries = 10  # 10 retries = ~10 seconds
                for attempt in range(max_retries):
                    try:
                        entries = st.session_state.api_client.get_entries(limit=10)
                        for entry in entries:
                            if entry.get('metadata', {}).get('answer_event_id') == event_id:
                                verification_data = entry.get('verification')
                                reward_data = entry.get('reward')
                                break

                        # If we found verification data, stop retrying
                        if verification_data:
                            break

                        # Wait 1 second before next retry
                        time.sleep(1)
                    except:
                        # Wait and retry
                        time.sleep(1)

            # Add to chat history
            chat_item = {
                'question': st.session_state.current_question,
                'answer': result.get('answer', ''),
                'contexts': result.get('contexts', []),
                'metadata': result.get('metadata', {}),
                'timestamp': datetime.now().strftime("%H:%M"),
                'verification': verification_data,
                'reward': reward_data
            }

            st.session_state.chat_history.append(chat_item)

            # Reset processing state
            st.session_state.processing = False
            st.session_state.current_question = ""
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.processing = False
            st.session_state.current_question = ""
            time.sleep(2)
            st.rerun()


if __name__ == "__main__":
    main()

