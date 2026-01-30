"""
MCP server for ASR Service with Speaker Diarization.
"""
import argparse
import os
import json
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
import torchaudio

from app.asr_service import WhisperASR
from app.logger import init_logger


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


def _validate_audio_path(audio_path: str) -> Path:
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if path.suffix.lower() not in {".wav", ".mp3"}:
        raise ValueError("Unsupported audio format, only .wav and .mp3 are supported")
    return path


def create_mcp(host: str, port: int) -> FastMCP:
    mcp = FastMCP("ASR Service", json_response=True, host=host, port=port)

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
            path = _validate_audio_path(audio_path)
            logger.info(f"Transcribing audio from {path}")
            
            # Initialize ASR service if needed
            asr_service = get_asr_service()
            
            # Load audio
            audio, sr = torchaudio.load(str(path))
            
            # Transcribe audio
            segments = asr_service.transcribe(audio, sr, language, chunk_length, "mcp", str(path))
            
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

            # Initialize ASR service if needed
            asr_service = get_asr_service()
            audio_path = asr_service.download_audio(audio_url, "mcp")
            try:
                return transcribe_audio(audio_path, language, chunk_length, output_format)
            finally:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
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

    return mcp


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASR Service MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host for SSE transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind port for SSE transport (default: 8000)",
    )
    return parser.parse_args(argv)


def run_server(transport: str, host: str, port: int) -> None:
    mcp = create_mcp(host=host, port=port)
    if transport == "stdio":
        mcp.run()
        return
    if transport == "sse":
        mcp.run(transport="sse")
        return
    raise ValueError(f"Unsupported transport: {transport}")


def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)
    run_server(args.transport, args.host, args.port)


if __name__ == "__main__":
    main()