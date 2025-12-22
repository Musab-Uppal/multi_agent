import os
import json
import requests
import google.generativeai as genai
from typing import Dict, Any
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

class VideoSearchTool:
    """Tool 1: Search for YouTube videos using SerpApi (Direct API call)"""
    
    def __init__(self):
        self.api_key = os.getenv("SERP_API_KEY")
        self.base_url = "https://serpapi.com/search"
        
    def search_video(self, query: str, num_results: int = 1) -> Dict[str, Any]:
        """Search for YouTube videos and return URLs using direct API call"""
        try:
            if not self.api_key:
                return {
                    "success": False, 
                    "error": "SERP_API_KEY not configured. Please add it to your .env file.",
                    "results": []
                }
            
            params = {
                "engine": "youtube",
                "search_query": query,
                "api_key": self.api_key,
                "num": num_results
            }
            
            # Make direct API call - NO external package dependency
            response = requests.get(self.base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: Status {response.status_code}",
                    "results": []
                }
            
            data = response.json()
            
            video_results = []
            if "video_results" in data:
                for video in data["video_results"][:num_results]:
                    if isinstance(video, dict):
                        # Get channel name - handle different formats
                        channel_info = video.get("channel", {})
                        if isinstance(channel_info, dict):
                            channel_name = channel_info.get("name", "Unknown")
                        else:
                            channel_name = str(channel_info) if channel_info else "Unknown"
                        
                        video_info = {
                            "title": video.get("title", "No Title"),
                            "link": video.get("link"),
                            "channel": channel_name,
                            "duration": video.get("duration", "N/A"),
                            "views": video.get("views", "N/A"),
                            "thumbnail": video.get("thumbnail"),
                            "description": str(video.get("description", ""))[:100] + "..."
                        }
                        video_results.append(video_info)
            
            return {
                "success": True,
                "results": video_results,
                "count": len(video_results),
                "query": query
            }
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out after 30 seconds", "results": []}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error. Check your internet.", "results": []}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request error: {str(e)}", "results": []}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}", "results": []}


class TranscriptionTool:
    """Tool 2: Transcribe YouTube videos using Gemini"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            print("⚠️  GEMINI_API_KEY not found in .env file")
            self.model = None
    
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """Get video information using yt-dlp"""
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                title = info.get('title', 'Unknown Title')
                description = info.get('description', 'No description')
                duration = info.get('duration', 0)
                
                # Format duration
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    hours, minutes = divmod(minutes, 60)
                    if hours > 0:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "N/A"
                
                return {
                    "success": True,
                    "title": title,
                    "description": description[:1000],  # Limit description length
                    "duration": duration_str,
                    "url": video_url,
                    "channel": info.get('channel', 'Unknown Channel'),
                    "view_count": info.get('view_count', 0),
                    "upload_date": info.get('upload_date', 'Unknown'),
                    "categories": info.get('categories', [])
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def transcribe_video(self, video_url: str) -> Dict[str, Any]:
        """Generate transcript/summary using available video information"""
        try:
            # Get video information
            video_info = self.get_video_info(video_url)
            if not video_info["success"]:
                return {
                    "success": False,
                    "error": f"Failed to get video info: {video_info.get('error')}",
                    "video_url": video_url
                }
            
            # If Gemini is not available, return basic info
            if not self.model:
                return {
                    "success": True,
                    "transcription": f"""Video Title: {video_info['title']}
Channel: {video_info['channel']}
Duration: {video_info['duration']}

Description:
{video_info['description']}

[Note: Gemini API key not configured. Add GEMINI_API_KEY to .env for AI-powered transcription]""",
                    "video_title": video_info['title'],
                    "video_url": video_url,
                    "raw_data": video_info
                }
            
            # Prepare prompt for Gemini
            prompt = f"""You are analyzing a YouTube video. Create a comprehensive transcript/summary based on the video information.

VIDEO INFORMATION:
Title: {video_info['title']}
Channel: {video_info['channel']}
Duration: {video_info['duration']}
Views: {video_info['view_count']}
Upload Date: {video_info['upload_date']}
URL: {video_url}

VIDEO DESCRIPTION:
{video_info['description']}

Please provide:
1. A detailed summary of what the video covers
2. Key topics and sections (imagine timestamps if needed)
3. Main takeaways and insights
4. Any notable points from the description

Format this as a useful transcript that someone could read to understand the video content."""

            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "transcription": response.text,
                "video_title": video_info['title'],
                "video_url": video_url,
                "raw_data": video_info,
                "model_used": "Gemini 1.5 Flash"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "video_url": video_url}


# Add this to tools.py to check available models

def list_available_models():
    """List all available Gemini models"""
    import google.generativeai as genai
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model.name}")
        return [model.name for model in models]
    else:
        print("No API key found")
        return []


  