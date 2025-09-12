import asyncio
import httpx
from typing import Optional
from config.settings import get_settings

class TTSService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.settings.elevenlabs_api_key
        }
    
    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Convert text to speech using ElevenLabs API"""
        try:
            if not voice_id:
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.35,          # يقلل الثبات ليعطي تنويع أكثر في الصوت
                    "similarity_boost": 0.7,    # يحافظ على وضوح وقرب من نبرة الصوت الأصلية
                    "style": 0.8,               # يزيد الحماس والتفاعل
                    "use_speaker_boost": True   # يضيف قوة ووضوح في النبرة
                }
            }

            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=self.headers)
                
                if response.status_code == 200:
                    return response.content
                else:
                    print(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    raise Exception(f"TTS API error: {response.status_code}")
                    
        except Exception as e:
            print(f"Error in text_to_speech: {e}")
            raise
    
    async def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs"""
        try:
            url = f"{self.base_url}/voices"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers={
                    "xi-api-key": self.settings.elevenlabs_api_key
                })
                
                if response.status_code == 200:
                    return response.json().get("voices", [])
                else:
                    print(f"Error getting voices: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error getting voices: {e}")
            return []
    
    async def get_voice_info(self, voice_id: str) -> dict:
        """Get information about a specific voice"""
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers={
                    "xi-api-key": self.settings.elevenlabs_api_key
                })
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error getting voice info: {response.status_code}")
                    return {}
                    
        except Exception as e:
            print(f"Error getting voice info: {e}")
            return {}