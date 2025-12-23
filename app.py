import streamlit as st
import os
from datetime import datetime
from agents import OrchestratorAgent, TranscriptionAgent
from knowledge_base import KnowledgeBase
from dotenv import load_dotenv
from tools import list_available_models
# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Video Search & Transcription Agent",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS with better visibility
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #374151;
        margin-top: 1.5rem;
    }
    .video-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #3B82F6;
    }
    .transcription-box {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 14px;
        line-height: 1.6;
        color: #111827;  /* Dark gray for better readability */
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .transcription-text {
        white-space: pre-wrap;
        word-wrap: break-word;
        color: #111827 !important;
        font-weight: 400;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #10B981;
        color: #065F46;
    }
    .dark-text {
        color: #111827 !important;
        font-weight: 500;
    }
    .transcription-header {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize agents
@st.cache_resource
def get_orchestrator():
    return OrchestratorAgent()

@st.cache_resource
def get_knowledge_base():
    return KnowledgeBase()

def main():
    st.markdown('<h1 class="main-header">🎬 AI Video Search & Transcription Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=100)
        st.title("Navigation")
        
        menu = st.selectbox(
            "Select Mode",
            ["🔍 Search & Transcribe", "📚 Knowledge Base"]
        )
        
        st.divider()
        
        st.markdown("### 📊 Stats")
        kb = get_knowledge_base()
        transcripts = kb.list_transcriptions()
        st.metric("Total Transcripts", len(transcripts))
        
        st.divider()
        
        
        serpapi_key = os.getenv("SERP_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        col1, col2 = st.columns(2)
        with col1:
            st.status("SerpApi", state="complete" if serpapi_key else "error")
        with col2:
            st.status("Gemini", state="complete" if gemini_key else "error")
    
    # Main content based on menu selection
    if menu == "🔍 Search & Transcribe":
        show_search_interface()
    elif menu == "📚 Knowledge Base":
        show_knowledge_base()

def show_search_interface():
    st.markdown('<h2 class="sub-header">🔍 Search for Videos and Get Transcripts</h2>', unsafe_allow_html=True)
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Enter search query",
            placeholder="e.g., Basics of Python",
            key="search_input"
        )
    with col2:
        num_results = st.number_input("Results", min_value=1, max_value=5, value=1)
    
    # Search button
    if st.button("🎬 Search & Transcribe", type="primary", use_container_width=True):
        if not search_query:
            st.warning("Please enter a search query")
            return
        
        if not os.getenv("SERP_API_KEY") or not os.getenv("GEMINI_API_KEY"):
            st.error("API keys not configured. Please check Settings.")
            return
        
        with st.spinner("Searching for videos..."):
            orchestrator = get_orchestrator()
            result = orchestrator.process_query(search_query)
            
            if result["success"]:
                st.success("✅ Transcription completed successfully!")
                # Show extracted main content (if available)
                main_content = result.get("main_content") or ""
                if main_content:
                    st.markdown("### ✨ Main Content")
                    st.markdown(f'<div class="success-box">{main_content}</div>', unsafe_allow_html=True)
                
                # Display transcription FIRST
                st.markdown("### 📝 Transcription")
                st.markdown('<div class="transcription-header">Full Transcript</div>', unsafe_allow_html=True)
                
                # Display transcription with better styling
                with st.expander("View Full Transcription", expanded=True):
                    # Wrap transcription text in a div with specific styling
                    transcription_html = f"""
                    <div class="transcription-box">
                        <div class="transcription-text">
                            {result["transcription"]}
                        </div>
                    </div>
                    """
                    st.markdown(transcription_html, unsafe_allow_html=True)
                
                # Download option
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Transcription",
                        data=result["transcription"],
                        file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                with col2:
                    st.info(f"Saved to: {result.get('saved_path', 'Knowledge base')}")
                
                # Display video results AFTER transcription
                st.markdown("### 📺 Search Results")
                st.info(f"Found {len(result.get('search_results', []))} video(s) for your search query.")
                
                for i, video in enumerate(result.get("search_results", [])):
                    with st.container():
                        st.markdown(f"""
                        <div class="video-card">
                            <h4>🎥 {video.get('title', 'No title')}</h4>
                            <p><strong>Channel:</strong> {video.get('channel', 'Unknown')}</p>
                            <p><strong>Duration:</strong> {video.get('duration', 'N/A')} | 
                            <strong>Views:</strong> {video.get('views', 'N/A')}</p>
                            <a href="{video.get('link')}" target="_blank">Watch on YouTube ↗</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
            else:
                st.error(f"Error: {result.get('error', 'Unknown error')}")

def show_knowledge_base():
    st.markdown('<h2 class="sub-header">📚 Saved Transcripts</h2>', unsafe_allow_html=True)
    
    kb = get_knowledge_base()
    transcripts = kb.list_transcriptions()
    
    if not transcripts:
        st.info("No transcripts saved yet. Start by searching for videos!")
        return
    
    # Filter and search
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search transcripts", placeholder="Enter keywords...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Title"])
    
    # Filter transcripts
    filtered_transcripts = transcripts
    if search_term:
        filtered_transcripts = [t for t in transcripts if search_term.lower() in t["title"].lower()]
    
    # Sort transcripts
    if sort_by == "Date (Newest)":
        filtered_transcripts.sort(key=lambda x: x["date"], reverse=True)
    elif sort_by == "Date (Oldest)":
        filtered_transcripts.sort(key=lambda x: x["date"])
    elif sort_by == "Title":
        filtered_transcripts.sort(key=lambda x: x["title"].lower())
    
    # Display transcripts
    for transcript in filtered_transcripts:
        with st.expander(f"📄 {transcript['title']}"):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**Date:** {transcript['date'][:10]}")
                st.write(f"**URL:** {transcript['url'][:50]}...")
            
            with col2:
                if st.button("📖 View", key=f"view_{transcript['filename']}"):
                    data = kb.load_transcription(transcript['filename'])
                    st.session_state[f"viewing_{transcript['filename']}"] = data
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{transcript['filename']}"):
                    # Delete the transcription file and clear any viewing state
                    deleted = kb.delete_transcription(transcript['filename'])
                    if deleted:
                        view_key = f"viewing_{transcript['filename']}"
                        if view_key in st.session_state:
                            del st.session_state[view_key]
                        st.success("Deleted transcription.")
                        st.rerun()
                    else:
                        st.error("Failed to delete transcription (file not found or permission error).")
    
    # Display selected transcript
    for transcript in filtered_transcripts:
        key = f"viewing_{transcript['filename']}"
        if key in st.session_state and st.session_state[key]:
            data = st.session_state[key]
            st.divider()
            st.markdown(f"### 📝 {data.get('metadata', {}).get('title', 'Transcript')}")
            # Show stored main content if present
            main_preview = data.get("main_content", "")
            if main_preview:
                st.markdown("### ✨ Main Content")
                st.markdown(f'<div class="success-box">{main_preview}</div>', unsafe_allow_html=True)

            # Display transcription with better styling
            st.markdown('<div class="transcription-header">Full Transcript</div>', unsafe_allow_html=True)
            transcription_html = f"""
            <div class="transcription-box">
                <div class="transcription-text">
                    {data.get("transcription", "")}
                </div>
            </div>
            """
            st.markdown(transcription_html, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download",
                    data=data.get("transcription", ""),
                    file_name=f"{transcript['filename'].replace('.json', '.txt')}",
                    mime="text/plain",
                    key=f"dl_{transcript['filename']}"
                )
            with col2:
                if st.button("Close", key=f"close_{transcript['filename']}"):
                    del st.session_state[key]
                    st.rerun()



if __name__ == "__main__":
    main()