"""
Q&A Chat Page

Beautiful chat interface for asking questions about PDF documents.
"""

import streamlit as st
from datetime import datetime


def render():
    """Render Q&A chat page."""
    st.markdown("# 💬 Q&A Chat")
    
    st.markdown("""
    <div class='custom-card'>
        <p>Ask questions about your uploaded PDF documents. The system will retrieve relevant context
        and generate accurate answers using RAG (Retrieval-Augmented Generation).</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history):
                # User message
                st.markdown(f"""
                <div class='chat-message user'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <div style='font-weight: 600; margin-right: 0.5rem;'>👤 You</div>
                        <div style='font-size: 0.75rem; opacity: 0.8;'>{chat['timestamp']}</div>
                    </div>
                    <div>{chat['question']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Assistant message
                st.markdown(f"""
                <div class='chat-message assistant'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <div style='font-weight: 600; margin-right: 0.5rem;'>🤖 Assistant</div>
                        <div style='font-size: 0.75rem; opacity: 0.8;'>{chat['timestamp']}</div>
                    </div>
                    <div>{chat['answer']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show contexts in expander
                if chat.get('contexts'):
                    with st.expander(f"📚 View context sources ({len(chat['contexts'])} chunks)"):
                        for j, context in enumerate(chat['contexts'], 1):
                            st.markdown(f"**Chunk {j}:**")
                            st.text(context[:300] + "..." if len(context) > 300 else context)
                            st.markdown("---")
        else:
            st.info("👋 No messages yet. Start by asking a question below!")
    
    # Input area
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])

    with col1:
        question = st.text_input(
            "Ask a question",
            placeholder="e.g., What is the price of Taj Mahal Palace?",
            label_visibility="collapsed",
            key="question_input",
            on_change=None  # Will be handled by form submission
        )

    with col2:
        ask_button = st.button("🚀 Ask", use_container_width=True, type="primary")

    # Handle question submission (button click OR enter key in text input)
    # Streamlit reruns on text_input change, so we check if question changed
    if "last_question" not in st.session_state:
        st.session_state.last_question = ""

    # Detect if user pressed Enter (question changed and is not empty)
    question_submitted = False
    if question and question != st.session_state.last_question:
        question_submitted = True
        st.session_state.last_question = question

    # Also submit if button clicked
    if ask_button and question:
        question_submitted = True

    if question_submitted and question:
        with st.spinner("🤔 Thinking..."):
            try:
                # Call API
                result = st.session_state.api_client.ask_question(
                    question=question,
                    collection_name="documents"
                )
                
                # Add to chat history
                chat_entry = {
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "question": question,
                    "answer": result.get("answer", "No answer generated"),
                    "contexts": result.get("contexts", []),
                    "event_id": result.get("event_id")
                }
                st.session_state.chat_history.append(chat_entry)
                
                # Success message
                st.success("✅ Answer generated!")
                
                # Rerun to show new message
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Clear chat button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("📥 Export Chat", use_container_width=True):
            if st.session_state.chat_history:
                # Create export data
                export_text = "# RLVR PDF Chat Export\n\n"
                for chat in st.session_state.chat_history:
                    export_text += f"## Q: {chat['question']}\n\n"
                    export_text += f"**A:** {chat['answer']}\n\n"
                    export_text += f"*Time: {chat['timestamp']}*\n\n"
                    export_text += "---\n\n"
                
                st.download_button(
                    label="💾 Download",
                    data=export_text,
                    file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            else:
                st.warning("No chat history to export")
    
    # Stats
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💬 Questions Asked",
            value=len(st.session_state.chat_history)
        )
    
    with col2:
        total_contexts = sum(len(chat.get('contexts', [])) for chat in st.session_state.chat_history)
        st.metric(
            label="📚 Contexts Retrieved",
            value=total_contexts
        )
    
    with col3:
        avg_contexts = total_contexts / len(st.session_state.chat_history) if st.session_state.chat_history else 0
        st.metric(
            label="📈 Avg Contexts/Question",
            value=f"{avg_contexts:.1f}"
        )

