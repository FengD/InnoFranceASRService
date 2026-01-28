"""
CLI tool for ASR Service with Speaker Diarization.
"""
import os
import sys
import json
from pathlib import Path

import click
import torch
import torchaudio

from app.asr_service import WhisperASR, SUPPORTED_AUDIO_EXT
from app.logger import init_logger


logger = init_logger("asr_cli", os.getenv("LOG_LEVEL", "INFO"))


@click.command()
@click.argument("audio_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--language",
    "-l",
    "language",
    type=str,
    default="fr",
    help="Language code for transcription (default: fr)"
)
@click.option(
    "--chunk-length",
    "-c",
    "chunk_length",
    type=int,
    default=30,
    help="Chunk length in seconds (default: 30)"
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path. If not specified, prints to stdout."
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    help="Output format (json or text)"
)
def main(audio_path: Path, language: str, chunk_length: int, output_path: Path, output_format: str):
    """
    Transcribe audio file using ASR Service with Speaker Diarization.
    
    AUDIO_PATH: Path to the audio file to transcribe (.wav or .mp3)
    """
    try:
        if audio_path.suffix.lower() not in SUPPORTED_AUDIO_EXT:
            raise click.ClickException("Unsupported audio format, only .wav and .mp3 are supported")

        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Initialize ASR service
        model_path = os.getenv("WHISPER_MODEL_PATH", "openai/whisper-large-v3")
        asr = WhisperASR(model_path, logger)
        
        # Load audio
        logger.info(f"Loading audio from {audio_path}")
        audio, sr = torchaudio.load(str(audio_path))
        
        # Transcribe audio
        logger.info("Starting transcription...")
        segments = asr.transcribe(audio, sr, language, chunk_length, "cli", str(audio_path))
        
        # Format output
        result = {
            "language": language,
            "segments": segments
        }
        
        # Output result
        if output_format == "text":
            # Simple text output
            text_output = "\n".join([seg["text"] for seg in segments])
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text_output)
                logger.info(f"Text output saved to {output_path}")
            else:
                print(text_output)
        else:
            # JSON output
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"JSON output saved to {output_path}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
        logger.info("Transcription completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()