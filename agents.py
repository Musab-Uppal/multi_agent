from typing import Dict, Any
from tools import VideoSearchTool, TranscriptionTool
from knowledge_base import KnowledgeBase

class VideoSearchAgent:
    """Agent responsible for searching videos"""
    
    def __init__(self):
        self.search_tool = VideoSearchTool()
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Execute video search"""
        print(f"🔍 Searching for videos: {query}")
        results = self.search_tool.search_video(query)
        return results

class TranscriptionAgent:
    """Agent responsible for transcribing videos"""
    
    def __init__(self):
        self.transcription_tool = TranscriptionTool()
        self.knowledge_base = KnowledgeBase()
    
    def execute(self, video_url: str, video_title: str = "") -> Dict[str, Any]:
        """Execute video transcription"""
        print(f"🎬 Transcribing video: {video_url}")
        
        # Get transcription
        result = self.transcription_tool.transcribe_video(video_url)
        
        if result["success"]:
            # Derive a short "main content" summary from the transcription
            main_content = self._extract_main_content(result.get("transcription", ""))

            # Save to knowledge base (include main_content)
            video_data = {
                "video_title": video_title or result.get("video_title", "Unknown"),
                "video_url": video_url,
                "raw_data": result.get("raw_data", {}),
                "main_content": main_content
            }

            saved_path = self.knowledge_base.save_transcription(video_data, result["transcription"])

            if saved_path:
                result["saved_path"] = saved_path
                print(f"✅ Transcription saved to: {saved_path}")

            # Attach main_content to the returned result so UI can show it immediately
            result["main_content"] = main_content
        
        return result

    def _extract_main_content(self, transcription: str) -> str:
        """Try to extract a concise "main content" block from the transcription.

        Strategy:
        - Look for common headings such as "Main takeaways" or "Main takeaways and insights".
        - If found, return the paragraph(s) following the heading.
        - Otherwise, return the first ~400 characters (trimmed to sentence boundary).
        """
        if not transcription:
            return ""

        lowered = transcription.lower()
        # Look for explicit sections
        markers = ["main takeaways", "main takeaways and insights", "main takeaways:", "key takeaways", "takeaways", "main takeaways and insights:"]
        for m in markers:
            idx = lowered.find(m)
            if idx != -1:
                # Find the original-cased index from transcription
                start = idx + len(m)
                # Extract following text up to a reasonable length
                snippet = transcription[start:start+800].strip()
                # Trim leading punctuation/colon/newlines
                snippet = snippet.lstrip(':\n\r ')
                # Return up to the first double newline or 400 chars
                parts = snippet.split('\n\n')
                candidate = parts[0].strip()
                if len(candidate) > 400:
                    candidate = candidate[:400].rsplit(' ', 1)[0] + '...'
                return candidate

        # Fallback: first 2-3 sentences or ~400 chars
        import re
        sentences = re.split(r'(?<=[.!?])\s+', transcription.strip())
        if len(sentences) >= 3:
            candidate = ' '.join(sentences[:3]).strip()
        else:
            candidate = transcription.strip()[:400]

        if len(candidate) > 400:
            candidate = candidate[:400].rsplit(' ', 1)[0] + '...'

        return candidate

class OrchestratorAgent:
    """Main agent that orchestrates the workflow"""
    
    def __init__(self):
        self.search_agent = VideoSearchAgent()
        self.transcription_agent = TranscriptionAgent()
        self.knowledge_base = KnowledgeBase()
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Complete workflow: Search → Transcribe → Store"""
        print(f"🚀 Starting workflow for query: {query}")
        
        # Step 1: Search for videos
        search_result = self.search_agent.execute(query)
        
        if not search_result["success"] or not search_result["results"]:
            return {"success": False, "error": "No videos found", "step": "search"}
        
        # Get first video result
        video = search_result["results"][0]
        video_url = video["link"]
        video_title = video["title"]
        
        # Step 2: Transcribe the video
        transcription_result = self.transcription_agent.execute(video_url, video_title)
        
        if not transcription_result["success"]:
            return {"success": False, "error": transcription_result.get("error"), "step": "transcription"}
        
        # Step 3: Return complete result
        return {
            "success": True,
            "search_results": search_result["results"],
            "transcription": transcription_result["transcription"],
            "video_title": video_title,
            "video_url": video_url,
            "saved_path": transcription_result.get("saved_path"),
            "raw_transcription": transcription_result
        }