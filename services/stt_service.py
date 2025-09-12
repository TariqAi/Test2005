import asyncio
import openai
import io
import tempfile
import os
from typing import Union
from config.settings import get_settings

class STTService:
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
    
    async def speech_to_text(self, audio_data: Union[bytes, io.BytesIO], language: str = "ar") -> str:
        """Convert speech to text using OpenAI Whisper API"""
        try:
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                if isinstance(audio_data, bytes):
                    temp_file.write(audio_data)
                else:
                    temp_file.write(audio_data.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # Open the temporary file and send to Whisper API
                with open(temp_file_path, "rb") as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        response_format="text"
                    )
                
                return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Error in speech_to_text: {e}")
            raise
    
    async def speech_to_text_with_translation(self, audio_data: Union[bytes, io.BytesIO]) -> dict:
        """Convert speech to text and translate to English if needed"""
        try:
            # Create a temporary file for the audio data
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                if isinstance(audio_data, bytes):
                    temp_file.write(audio_data)
                else:
                    temp_file.write(audio_data.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # Get transcription
                with open(temp_file_path, "rb") as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
                
                # Get translation if not in English
                translation = None
                if transcript.language != "en":
                    with open(temp_file_path, "rb") as audio_file:
                        translation_result = await self.client.audio.translations.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"
                        )
                    translation = translation_result.strip() if isinstance(translation_result, str) else translation_result.text.strip()
                
                return {
                    "text": transcript.text,
                    "language": transcript.language,
                    "translation": translation
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            print(f"Error in speech_to_text_with_translation: {e}")
            raise
    
    async def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate if the audio data is in a supported format"""
        try:
            # Check for common audio file headers
            # WAV file header
            if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
                return True
            # MP3 file header
            if audio_data[:3] == b'ID3' or audio_data[:2] == b'\xff\xfb':
                return True
            # M4A/MP4 file header
            if b'ftyp' in audio_data[:20]:
                return True
            # OGG file header
            if audio_data[:4] == b'OggS':
                return True
            
            return False
            
        except Exception as e:
            print(f"Error validating audio format: {e}")
            return False