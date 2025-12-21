import os
import json
from serpapi import GoogleSearch
import google.generativeai as genai
from typing import Dict, Any
import yt_dlp
import tempfile
from dotenv import load_dotenv

load_dotenv()

class VideoSearchTool:
    """Tool 1: Search for YouTube videos using SerpApi"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
    
    def search_video(self, query: str, num_results: int = 1) -> Dict[str, Any]:
        """Search for YouTube videos and return URLs"""
        try:
            params = {
                "engine": "youtube",
                "search_query": query,
                "api_key": self.api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            video_results = []
            if "video_results" in results:
                for video in results["video_results"][:num_results]:
                    video_info = {
                        "title": video.get("title"),
                        "link": video.get("link"),
                        "channel": video.get("channel", {}).get("name"),
                        "duration": video.get("duration"),
                        "views": video.get("views")
                    }
                    video_results.append(video_info)
            
            return {
                "success": True,
                "results": video_results,
                "count": len(video_results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class TranscriptionTool:
    """Tool 2: Transcribe YouTube videos using Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def extract_audio_from_video(self, video_url: str) -> str:
        """Download audio from YouTube video"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            audio_file = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
        return audio_file
    
    def transcribe_video(self, video_url: str) -> Dict[str, Any]:
        """Transcribe video content using Gemini"""
        try:
            # For Gemini API (if using video input directly)
            # Note: Gemini currently doesn't support direct video URL processing
            # We'll use audio transcription approach
            
            # Alternative approach using video description + transcripts
            # Using yt-dlp to get video info
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Get video description
                description = info.get('description', '')
                title = info.get('title', '')
                
                # Try to get subtitles
                subtitles = ''
                if 'en' in info.get('subtitles', {}):
                    subtitles_text = []
                    for sub in info['subtitles']['en']:
                        if 'text' in sub:
                            subtitles_text.append(sub['text'])
                    subtitles = ' '.join(subtitles_text)
                
                # Combine information for transcription
                video_content = f"""
                Video Title: {title}
                
                Video Description:
                {description}
                
                Transcript/Subtitles:
                {subtitles}
                """
                
                # Use Gemini to process and summarize
                prompt = f"""Please provide a detailed transcription and summary of this video content:
                
                {video_content}
                
                Provide:
                1. Complete transcription (if available)
                2. Key points summary
                3. Timestamps for important sections (if possible)
                """
                
                response = self.model.generate_content(prompt)
                
                return {
                    "success": True,
                    "transcription": response.text,
                    "video_title": title,
                    "video_url": video_url,
                    "raw_data": {
                        "description": description[:500] + "..." if len(description) > 500 else description,
                        "subtitles_available": bool(subtitles)
                    }
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}