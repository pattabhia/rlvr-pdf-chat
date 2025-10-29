"""
Training Data Page

View and export training datasets.
"""

import streamlit as st
import pandas as pd


def render():
    """Render training data page."""
    st.markdown("# 📊 Training Data Management")
    
    st.markdown("""
    <div class='custom-card'>
        <p>View, filter, and export training datasets collected from Q&A interactions.
        Training data includes questions, answers, verification scores, and reward scores.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Datasets", "🔍 Browse Entries", "📤 Export"])
    
    # Tab 1: Datasets Overview
    with tab1:
        st.markdown("### 📋 Available Datasets")
        
        try:
            datasets_data = st.session_state.api_client.list_datasets()
            datasets = datasets_data.get("datasets", [])
            
            if datasets:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        label="📁 Total Datasets",
                        value=datasets_data.get("total_datasets", 0)
                    )
                
                with col2:
                    st.metric(
                        label="📊 Total Entries",
                        value=f"{datasets_data.get('total_entries', 0):,}"
                    )
                
                with col3:
                    avg_score = sum(d.get("avg_verification_score", 0) for d in datasets) / len(datasets)
                    st.metric(
                        label="⭐ Avg Verification Score",
                        value=f"{avg_score:.2f}"
                    )
                
                st.markdown("---")
                
                # Dataset cards
                for dataset in datasets:
                    with st.expander(f"📁 {dataset.get('file_name', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            **📊 Entries:** {dataset.get('num_entries', 0):,}  
                            **⭐ Avg Verification:** {dataset.get('avg_verification_score', 0):.2f}  
                            **🎯 Avg Reward:** {dataset.get('avg_reward_score', 0):.2f}  
                            """)
                        
                        with col2:
                            date_range = dataset.get('date_range', {})
                            st.markdown(f"""
                            **📅 Earliest:** {date_range.get('earliest', 'N/A')}  
                            **📅 Latest:** {date_range.get('latest', 'N/A')}  
                            **💾 Size:** {dataset.get('file_size_bytes', 0) / 1024:.2f} KB  
                            """)
                        
                        # Domains
                        domains = dataset.get('domains', [])
                        if domains:
                            st.markdown(f"**🏷️ Domains:** {', '.join(domains)}")
            else:
                st.info("📭 No datasets available yet. Start asking questions to generate training data!")
                
        except Exception as e:
            st.error(f"❌ Error loading datasets: {str(e)}")
    
    # Tab 2: Browse Entries
    with tab2:
        st.markdown("### 🔍 Browse Training Entries")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_verification = st.slider(
                "Min Verification Score",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        with col2:
            min_reward = st.slider(
                "Min Reward Score",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
        
        with col3:
            limit = st.number_input(
                "Max Entries",
                min_value=10,
                max_value=1000,
                value=50,
                step=10
            )
        
        # Fetch button
        if st.button("🔍 Search", type="primary", use_container_width=True):
            with st.spinner("🔍 Fetching entries..."):
                try:
                    entries = st.session_state.api_client.get_entries(
                        min_verification_score=min_verification if min_verification > 0 else None,
                        min_reward_score=min_reward if min_reward > 0 else None,
                        limit=limit
                    )
                    
                    if entries:
                        st.success(f"✅ Found {len(entries)} entries")
                        
                        # Display entries
                        for i, entry in enumerate(entries, 1):
                            with st.expander(f"Entry {i}: {entry.get('question', 'N/A')[:100]}..."):
                                st.markdown(f"**❓ Question:** {entry.get('question', 'N/A')}")
                                st.markdown(f"**💬 Answer:** {entry.get('answer', 'N/A')}")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    verification = entry.get('verification', {})
                                    st.markdown(f"""
                                    **✅ Verification:**
                                    - Faithfulness: {verification.get('faithfulness', 0):.2f}
                                    - Relevancy: {verification.get('relevancy', 0):.2f}
                                    - Overall: {verification.get('overall_score', 0):.2f}
                                    """)
                                
                                with col2:
                                    reward = entry.get('reward', {})
                                    st.markdown(f"""
                                    **🎯 Reward:**
                                    - Score: {reward.get('score', 0):.2f}
                                    - Domain: {reward.get('domain', 'N/A')}
                                    - Has GT: {reward.get('has_ground_truth', False)}
                                    """)
                    else:
                        st.info("📭 No entries found matching the criteria")
                        
                except Exception as e:
                    st.error(f"❌ Error fetching entries: {str(e)}")
    
    # Tab 3: Export
    with tab3:
        st.markdown("### 📤 Export Training Data")
        
        st.markdown("""
        <div class='custom-card'>
            <p>Export training data in different formats for fine-tuning:</p>
            <ul>
                <li><strong>DPO:</strong> Direct Preference Optimization (chosen/rejected pairs)</li>
                <li><strong>SFT:</strong> Supervised Fine-Tuning (prompt/completion pairs)</li>
                <li><strong>JSONL:</strong> Standard JSON Lines format</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                options=["dpo", "sft", "jsonl"],
                format_func=lambda x: {"dpo": "DPO (Preference)", "sft": "SFT (Supervised)", "jsonl": "JSONL (Standard)"}[x]
            )
        
        with col2:
            min_export_score = st.slider(
                "Min Quality Score",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Minimum verification score for export"
            )
        
        # Export button
        if st.button("📤 Export Dataset", type="primary", use_container_width=True):
            with st.spinner(f"📤 Exporting to {export_format.upper()} format..."):
                try:
                    result = st.session_state.api_client.export_dataset(
                        format=export_format,
                        min_verification_score=min_export_score
                    )
                    
                    st.success(f"✅ Export completed!")
                    
                    st.markdown(f"""
                    <div class='custom-card'>
                        <p><strong>📁 File:</strong> <code>{result.get('export_file', 'N/A')}</code></p>
                        <p><strong>📊 Entries:</strong> {result.get('num_entries', 0):,}</p>
                        <p><strong>📋 Format:</strong> {result.get('format', 'N/A').upper()}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Error exporting dataset: {str(e)}")

