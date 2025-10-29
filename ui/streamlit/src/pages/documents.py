"""
Documents Page

Upload and manage PDF documents.
"""

import streamlit as st


def render():
    """Render documents page."""
    st.markdown("# 📄 Document Management")
    
    st.markdown("""
    <div class='custom-card'>
        <p>Upload PDF documents to add them to the knowledge base. Documents are automatically
        processed, chunked, and embedded for semantic search.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Two columns: Upload and Collection Info
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF document to add to the knowledge base",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Show file info
            st.markdown(f"""
            <div class='custom-card'>
                <p><strong>📄 File:</strong> {uploaded_file.name}</p>
                <p><strong>📦 Size:</strong> {uploaded_file.size / 1024:.2f} KB</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Upload button
            if st.button("🚀 Upload & Process", type="primary", use_container_width=True):
                with st.spinner("📤 Uploading and processing document..."):
                    try:
                        # Read file bytes
                        file_bytes = uploaded_file.read()
                        
                        # Call API
                        result = st.session_state.api_client.ingest_document(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name
                        )
                        
                        # Success message
                        st.success(f"✅ {result.get('message', 'Document uploaded successfully!')}")
                        
                        # Show details
                        st.markdown(f"""
                        <div class='custom-card'>
                            <p><strong>📊 Chunks created:</strong> {result.get('num_chunks', 'N/A')}</p>
                            <p><strong>🗂️ Collection:</strong> {result.get('collection_name', 'N/A')}</p>
                            <p><strong>🆔 Event ID:</strong> <code>{result.get('event_id', 'N/A')}</code></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Rerun to update collection info
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error uploading document: {str(e)}")
    
    with col2:
        st.markdown("### 📊 Collection Info")
        
        try:
            collection_info = st.session_state.api_client.get_collection_info()
            
            st.markdown(f"""
            <div class='custom-card'>
                <h4>🗂️ {collection_info.get('collection_name', 'N/A')}</h4>
                <p><strong>📄 Total chunks:</strong> {collection_info.get('points_count', 0):,}</p>
                <p><strong>🔢 Vector count:</strong> {collection_info.get('vectors_count', 0):,}</p>
                <p><strong>📏 Dimensions:</strong> {collection_info.get('vector_dimension', 0)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics
            st.markdown("#### 📈 Metrics")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.metric(
                    label="📄 Document Chunks",
                    value=f"{collection_info.get('points_count', 0):,}"
                )
            
            with col_b:
                st.metric(
                    label="📏 Vector Dimension",
                    value=collection_info.get('vector_dimension', 0)
                )
            
        except Exception as e:
            st.error(f"❌ Error fetching collection info: {str(e)}")
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📚 How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='custom-card'>
            <h4>1️⃣ Upload</h4>
            <p>Upload your PDF document using the file uploader above.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='custom-card'>
            <h4>2️⃣ Process</h4>
            <p>The system extracts text, chunks it, and generates embeddings.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='custom-card'>
            <h4>3️⃣ Query</h4>
            <p>Ask questions in the Q&A Chat page to retrieve relevant information.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Technical details
    st.markdown("---")
    with st.expander("🔧 Technical Details"):
        st.markdown("""
        **Document Processing Pipeline:**
        
        1. **PDF Extraction**: Text is extracted from PDF using `pdfplumber`
        2. **Text Chunking**: Text is split into chunks using `RecursiveCharacterTextSplitter`
           - Chunk size: 1000 characters
           - Chunk overlap: 200 characters
        3. **Embedding Generation**: Chunks are embedded using `sentence-transformers`
           - Model: `all-MiniLM-L6-v2`
           - Dimension: 384
        4. **Vector Storage**: Embeddings are stored in Qdrant vector database
        5. **Event Publishing**: `document.ingested` event is published to RabbitMQ
        
        **Supported Formats:**
        - PDF (.pdf)
        
        **Limitations:**
        - Maximum file size: 50 MB
        - Text-based PDFs only (scanned PDFs require OCR)
        """)

