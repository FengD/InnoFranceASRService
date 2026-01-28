"""
MCP server for ASR Service with Speaker Diarization.
"""
import os
import json
import tempfile
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
import torch
import torchaudio
import requests
from urllib.parse import urlparse

from app.asr_service import WhisperASR
from app.logger import init_logger


mcp = FastMCP("ASR Service", json_response=True)
logger = init_logger("asr_mcp", os.getenv("LOG_LEVEL", "INFO"))

# Global ASR service instance
asr = None


def get_asr_service():
    """Lazy initialization of ASR service"""
    global asr
    if asr is None:
        model_path = os.getenv("WHISPER_MODEL_PATH", "openai/whisper-large-v3")
        asr = WhisperASR(model_path, logger)
    return asr


@mcp.tool()
def transcribe_audio(
    audio_path: str,
    language: str = "fr",
    chunk_length: int = 30,
    output_format: str = "json"
) -> dict:
    """
    Transcribe an audio file using ASR Service with Speaker Diarization.
    
    Args:
        audio_path: Path to the audio file to transcribe (.wav or .mp3)
        language: Language code for transcription (default: fr)
        chunk_length: Chunk length in seconds (default: 30)
        output_format: Output format ('json' or 'text')
        
    Returns:
        Dictionary with 'success', 'result', and optional 'error' keys
    """
    try:
        logger.info(f"Transcribing audio from {audio_path}")
        
        # Initialize ASR service if needed
        asr_service = get_asr_service()
        
        # Load audio
        audio, sr = torchaudio.load(audio_path)
        
        # Transcribe audio
        segments = asr_service.transcribe(audio, sr, language, chunk_length, "mcp")
        
        # Format output
        result = {
            "language": language,
            "segments": segments
        }
        
        if output_format == "text":
            # Simple text output
            text_output = "\n".join([seg["text"] for seg in segments])
            return {
                "success": True,
                "result": text_output
            }
        else:
            # JSON output
            return {
                "success": True,
                "result": result
            }
            
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        return {
            "success": False,
            "error": f"Transcription failed: {str(e)}"
        }


@mcp.tool()
def transcribe_audio_from_url(
    audio_url: str,
    language: str = "fr",
    chunk_length: int = 30,
    output_format: str = "json"
) -> dict:
    """
    Download and transcribe an audio file from URL using ASR Service with Speaker Diarization.
    
    Args:
        audio_url: URL to the audio file to transcribe (.wav or .mp3)
        language: Language code for transcription (default: fr)
        chunk_length: Chunk length in seconds (default: 30)
        output_format: Output format ('json' or 'text')
        
    Returns:
        Dictionary with 'success', 'result', and optional 'error' keys
    """
    try:
        logger.info(f"Downloading and transcribing audio from {audio_url}")
        
        # Validate URL
        p = urlparse(audio_url)
        if p.scheme not in ("http", "https"):
            raise ValueError("Invalid URL scheme")
            
        # Determine file extension
        ext = os.path.splitext(audio_url)[1].lower()
        if ext not in [".wav", ".mp3"]:
            raise ValueError("Unsupported audio format")
            
        # Download audio to temporary file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.close()
        
        headers = {
            "User-Agent": "curl/7.88.1",
            "Accept": "*/*"
        }
        
        try:
            with requests.get(audio_url, stream=True, timeout=30, headers=headers) as r:
                r.raise_for_status()
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        with open(tmp.name, "ab") as f:
                            f.write(chunk)
                            
            # Transcribe the downloaded audio
            result = transcribe_audio(tmp.name, language, chunk_length, output_format)
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
                
    except Exception as e:
        logger.error(f"Error downloading or transcribing audio: {e}")
        return {
            "success": False,
            "error": f"Download or transcription failed: {str(e)}"
        }


@mcp.tool()
def transcribe_and_save(
    audio_path: str,
    output_path: str,
    language: str = "fr",
    chunk_length: int = 30,
    output_format: str = "json"
) -> dict:
    """
    Transcribe an audio file and save the result to a file.
    
    Args:
        audio_path: Path to the audio file to transcribe (.wav or .mp3)
        output_path: Path where the transcription result will be saved
        language: Language code for transcription (default: fr)
        chunk_length: Chunk length in seconds (default: 30)
        output_format: Output format ('json' or 'text')
        
    Returns:
        Dictionary with 'success', 'output_path', and optional 'error' keys
    """
    try:
        logger.info(f"Transcribing audio from {audio_path} and saving to {output_path}")
        
        # Transcribe audio
        result_dict = transcribe_audio(audio_path, language, chunk_length, output_format)
        
        if not result_dict["success"]:
            return result_dict
            
        # Save result to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == "text" and isinstance(result_dict["result"], str):
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result_dict["result"])
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_dict["result"], f, ensure_ascii=False, indent=2)
                
        return {
            "success": True,
            "output_path": str(output_file)
        }
        
    except Exception as e:
        logger.error(f"Error saving transcription: {e}")
        return {
            "success": False,
            "error": f"Failed to save transcription: {str(e)}"
        }


if __name__ == "__main__":
    mcp.run()