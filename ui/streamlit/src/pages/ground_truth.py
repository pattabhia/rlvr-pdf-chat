"""
Ground Truth Page

Manage ground truth data for reward computation.
"""

import streamlit as st
import json


def render():
    """Render ground truth page."""
    st.markdown("# 🎯 Ground Truth Management")
    
    st.markdown("""
    <div class='custom-card'>
        <p>Manage ground truth data for different domains. Ground truth is used for reward computation
        and model evaluation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2 = st.tabs(["📋 Domains", "➕ Add Entry"])
    
    # Tab 1: View Domains
    with tab1:
        st.markdown("### 📋 Ground Truth Domains")
        
        try:
            domains_data = st.session_state.api_client.list_domains()
            domains = domains_data.get("domains", [])
            
            if domains:
                # Metrics
                st.metric(
                    label="🏷️ Total Domains",
                    value=len(domains)
                )
                
                st.markdown("---")
                
                # Domain cards
                for domain in domains:
                    with st.expander(f"🏷️ {domain.get('domain_name', 'Unknown')}"):
                        st.markdown(f"**📝 Description:** {domain.get('description', 'N/A')}")
                        st.markdown(f"**🆔 ID:** {domain.get('id', 'N/A')}")
                        st.markdown(f"**📅 Created:** {domain.get('created_at', 'N/A')}")
                        
                        # Metadata schema
                        metadata_schema = domain.get('metadata_schema', {})
                        if metadata_schema:
                            st.markdown("**🔧 Metadata Schema:**")
                            st.json(metadata_schema)
                        
                        # Fetch entries for this domain
                        if st.button(f"📄 View Entries", key=f"view_{domain.get('id')}"):
                            try:
                                entries = st.session_state.api_client.list_ground_truth_entries(
                                    domain=domain.get('domain_name'),
                                    limit=50
                                )
                                
                                if entries:
                                    st.markdown(f"**📊 Found {len(entries)} entries:**")
                                    
                                    for i, entry in enumerate(entries, 1):
                                        with st.container():
                                            st.markdown(f"**Entry {i}:**")
                                            st.markdown(f"- **Question:** {entry.get('question', 'N/A')}")
                                            st.markdown(f"- **Expected Answer:** {entry.get('expected_answer', 'N/A')}")
                                            
                                            metadata = entry.get('metadata', {})
                                            if metadata:
                                                st.markdown(f"- **Metadata:** {json.dumps(metadata, indent=2)}")
                                            
                                            st.markdown("---")
                                else:
                                    st.info("📭 No entries found for this domain")
                                    
                            except Exception as e:
                                st.error(f"❌ Error fetching entries: {str(e)}")
            else:
                st.info("📭 No domains available yet. Create a domain to get started!")
                
        except Exception as e:
            st.error(f"❌ Error loading domains: {str(e)}")
    
    # Tab 2: Add Entry
    with tab2:
        st.markdown("### ➕ Add Ground Truth Entry")
        
        # First, select or create domain
        st.markdown("#### 1️⃣ Select Domain")
        
        try:
            domains_data = st.session_state.api_client.list_domains()
            domains = domains_data.get("domains", [])
            domain_names = [d.get("domain_name") for d in domains]
            
            if domain_names:
                selected_domain = st.selectbox(
                    "Choose domain",
                    options=domain_names,
                    help="Select the domain for this ground truth entry"
                )
            else:
                st.warning("⚠️ No domains available. Create a domain first!")
                
                # Create domain form
                with st.expander("➕ Create New Domain"):
                    new_domain_name = st.text_input("Domain Name", placeholder="e.g., taj_hotels_pricing")
                    new_domain_desc = st.text_area("Description", placeholder="Ground truth for Taj Hotels pricing questions")
                    
                    # Metadata schema
                    st.markdown("**Metadata Schema (JSON):**")
                    metadata_schema_text = st.text_area(
                        "Schema",
                        value='{\n  "type": "price_range",\n  "currency": "INR"\n}',
                        height=150,
                        label_visibility="collapsed"
                    )
                    
                    if st.button("➕ Create Domain", type="primary"):
                        try:
                            metadata_schema = json.loads(metadata_schema_text)
                            
                            result = st.session_state.api_client.create_domain(
                                domain_name=new_domain_name,
                                description=new_domain_desc,
                                metadata_schema=metadata_schema
                            )
                            
                            st.success(f"✅ Domain '{new_domain_name}' created!")
                            st.rerun()
                            
                        except json.JSONDecodeError:
                            st.error("❌ Invalid JSON in metadata schema")
                        except Exception as e:
                            st.error(f"❌ Error creating domain: {str(e)}")
                
                selected_domain = None
            
            # Add entry form (only if domain is selected)
            if selected_domain:
                st.markdown("---")
                st.markdown("#### 2️⃣ Add Entry")
                
                question = st.text_input(
                    "Question",
                    placeholder="e.g., What is the price of Taj Mahal Palace?"
                )
                
                expected_answer = st.text_area(
                    "Expected Answer",
                    placeholder="e.g., {\"min_price\": 24000, \"max_price\": 65000, \"currency\": \"INR\"}",
                    help="Can be text or JSON"
                )
                
                # Metadata
                st.markdown("**Metadata (JSON, optional):**")
                metadata_text = st.text_area(
                    "Metadata",
                    value='{}',
                    height=100,
                    label_visibility="collapsed"
                )
                
                if st.button("➕ Add Entry", type="primary", use_container_width=True):
                    if question and expected_answer:
                        try:
                            # Try to parse expected_answer as JSON
                            try:
                                expected_answer_parsed = json.loads(expected_answer)
                            except:
                                expected_answer_parsed = expected_answer
                            
                            # Parse metadata
                            metadata = json.loads(metadata_text)
                            
                            result = st.session_state.api_client.create_ground_truth_entry(
                                domain=selected_domain,
                                question=question,
                                expected_answer=expected_answer_parsed,
                                metadata=metadata
                            )
                            
                            st.success(f"✅ Entry added to '{selected_domain}'!")
                            
                        except json.JSONDecodeError as e:
                            st.error(f"❌ Invalid JSON: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Error adding entry: {str(e)}")
                    else:
                        st.warning("⚠️ Please fill in both question and expected answer")
                        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

