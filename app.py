import streamlit as st
import os
from datetime import datetime
from agents import OrchestratorAgent, TranscriptionAgent
from knowledge_base import KnowledgeBase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Video Search & Transcription Agent",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS
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
        background-color: #F9FAFB;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        max-height: 500px;
        overflow-y: auto;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #10B981;
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
            ["🔍 Search & Transcribe", "📚 Knowledge Base", "⚙️ Settings"]
        )
        
        st.divider()
        
        st.markdown("### 📊 Stats")
        kb = get_knowledge_base()
        transcripts = kb.list_transcriptions()
        st.metric("Total Transcripts", len(transcripts))
        
        st.divider()
        
        st.markdown("### 🔑 API Status")
        serpapi_key = os.getenv("SERPAPI_API_KEY")
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
    elif menu == "⚙️ Settings":
        show_settings()

def show_search_interface():
    st.markdown('<h2 class="sub-header">🔍 Search for Videos and Get Transcripts</h2>', unsafe_allow_html=True)
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Enter search query",
            placeholder="e.g., Machine Learning Tutorial 2024",
            key="search_input"
        )
    with col2:
        num_results = st.number_input("Results", min_value=1, max_value=5, value=1)
    
    # Search button
    if st.button("🎬 Search & Transcribe", type="primary", use_container_width=True):
        if not search_query:
            st.warning("Please enter a search query")
            return
        
        if not os.getenv("SERPAPI_API_KEY") or not os.getenv("GEMINI_API_KEY"):
            st.error("API keys not configured. Please check Settings.")
            return
        
        with st.spinner("Searching for videos..."):
            orchestrator = get_orchestrator()
            result = orchestrator.process_query(search_query)
            
            if result["success"]:
                st.success("✅ Transcription completed successfully!")
                
                # Display video results
                st.markdown("### 📺 Search Results")
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
                
                # Display transcription
                st.markdown("### 📝 Transcription")
                with st.expander("View Full Transcription", expanded=True):
                    st.markdown(f'<div class="transcription-box">{result["transcription"]}</div>', unsafe_allow_html=True)
                
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
                    # Implement delete functionality
                    st.warning("Delete functionality to be implemented")
    
    # Display selected transcript
    for transcript in filtered_transcripts:
        key = f"viewing_{transcript['filename']}"
        if key in st.session_state and st.session_state[key]:
            data = st.session_state[key]
            st.divider()
            st.markdown(f"### 📝 {data.get('metadata', {}).get('title', 'Transcript')}")
            st.markdown(f'<div class="transcription-box">{data.get("transcription", "")}</div>', unsafe_allow_html=True)
            
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

def show_settings():
    st.markdown('<h2 class="sub-header">⚙️ API Configuration</h2>', unsafe_allow_html=True)
    
    st.warning("For security, API keys should be set in the `.env` file")
    
    with st.form("api_settings"):
        serpapi_key = st.text_input(
            "SerpApi API Key",
            value=os.getenv("SERPAPI_API_KEY", ""),
            type="password"
        )
        
        gemini_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password"
        )
        
        kb_path = st.text_input(
            "Knowledge Base Path",
            value=os.getenv("KNOWLEDGE_BASE_PATH", "./transcripts")
        )
        
        if st.form_submit_button("Save Configuration"):
            # Note: In production, save to .env file or database
            st.info("In production, implement saving to .env file or secure storage")
            st.success("Settings updated (demo mode)")
    
    st.divider()
    
    st.markdown("### 🛠️ Tools & Utilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Cache", type="secondary"):
            st.cache_resource.clear()
            st.success("Cache cleared!")
    
    with col2:
        if st.button("Test API Connections", type="secondary"):
            from tools import VideoSearchTool, TranscriptionTool
            
            try:
                search_tool = VideoSearchTool()
                test_result = search_tool.search_video("test", num_results=1)
                st.success(f"SerpApi: {'Connected' if test_result['success'] else 'Error'}")
            except:
                st.error("SerpApi: Connection failed")
            
            try:
                trans_tool = TranscriptionTool()
                st.success("Gemini: Initialized successfully")
            except:
                st.error("Gemini: Initialization failed")

if __name__ == "__main__":
    main()