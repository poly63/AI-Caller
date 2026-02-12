import numpy as np
import asyncio
from typing import AsyncGenerator, List, Dict
import logging

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


class TranscriptionService:
    """Real-time transcription service using Faster-Whisper"""
    
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize Whisper model
        
        Args:
            model_size: tiny, base, small, medium, large-v2, large-v3
            device: cpu or cuda
        """
        logger.info(f"Loading Whisper model: {model_size} on {device}")
        self.model = None
        if WhisperModel is not None:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16"
            )
        else:
            logger.warning("faster-whisper is not installed; transcription will return empty results")
        self.sample_rate = 16000
        
    def transcribe_audio(self, audio_data: np.ndarray) -> List[Dict]:
        """
        Transcribe audio data
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            List of segments with text, timestamps, and confidence
        """
        try:
            if self.model is None:
                return []

            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                )
            )
            
            results = []
            for segment in segments:
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": segment.avg_logprob
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return []
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        chunk_duration: float = 2.0
    ) -> AsyncGenerator[Dict, None]:
        """
        Transcribe streaming audio in real-time
        
        Args:
            audio_stream: Async generator yielding audio bytes
            chunk_duration: Duration of each chunk in seconds
            
        Yields:
            Transcription segments
        """
        buffer = []
        chunk_size = int(self.sample_rate * chunk_duration)
        
        async for audio_bytes in audio_stream:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            buffer.extend(audio_array)
            
            # Process when buffer is large enough
            if len(buffer) >= chunk_size:
                audio_chunk = np.array(buffer[:chunk_size])
                buffer = buffer[chunk_size:]
                
                # Transcribe chunk
                segments = await asyncio.to_thread(
                    self.transcribe_audio,
                    audio_chunk
                )
                
                for segment in segments:
                    yield segment
        
        # Process remaining buffer
        if buffer:
            audio_chunk = np.array(buffer)
            segments = await asyncio.to_thread(
                self.transcribe_audio,
                audio_chunk
            )
            for segment in segments:
                yield segment
    
    def transcribe_file(self, audio_file_path: str) -> str:
        """
        Transcribe complete audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Full transcript as string
        """
        if self.model is None:
            return ""
        segments, _ = self.model.transcribe(audio_file_path, language="en")
        return " ".join([segment.text.strip() for segment in segments])


# Global instance
_transcription_service = None


def get_transcription_service(
    model_size: str = "base",
    device: str = "cpu"
) -> TranscriptionService:
    """Get or create transcription service singleton"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService(model_size, device)
    return _transcription_service
