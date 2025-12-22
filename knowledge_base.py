import os
import json
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class KnowledgeBase:
    """Manages storage of transcriptions"""
    
    def __init__(self):
        self.base_path = os.getenv("KNOWLEDGE_BASE_PATH", "./transcripts")
        os.makedirs(self.base_path, exist_ok=True)
    
    def save_transcription(self, video_data: Dict[str, Any], transcription: str) -> str:
        """Save transcription to file

        Accepts optional `main_content` inside `video_data` or as keyword param.
        """
        try:
            # Create filename from video title and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in video_data.get("video_title", "unknown") 
                               if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_{timestamp}.json"
            filepath = os.path.join(self.base_path, filename)
            
            # Prepare data
            data = {
                "metadata": {
                    "title": video_data.get("video_title"),
                    "url": video_data.get("video_url"),
                    "saved_at": datetime.now().isoformat(),
                    "source": "youtube"
                },
                "transcription": transcription,
                "raw_data": video_data.get("raw_data", {}),
                "main_content": video_data.get("main_content", "")
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            print(f"Error saving transcription: {e}")
            return ""
    
    def list_transcriptions(self) -> list:
        """List all saved transcriptions"""
        files = []
        for file in os.listdir(self.base_path):
            if file.endswith('.json'):
                filepath = os.path.join(self.base_path, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        files.append({
                            "filename": file,
                            "title": data.get("metadata", {}).get("title", "Unknown"),
                            "date": data.get("metadata", {}).get("saved_at", ""),
                            "url": data.get("metadata", {}).get("url", "")
                        })
                except:
                    continue
        return files
    
    def load_transcription(self, filename: str) -> Dict[str, Any]:
        """Load a specific transcription"""
        filepath = os.path.join(self.base_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def delete_transcription(self, filename: str) -> bool:
        """Delete a saved transcription file. Returns True on success."""
        filepath = os.path.join(self.base_path, filename)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error deleting transcription {filepath}: {e}")
            return False