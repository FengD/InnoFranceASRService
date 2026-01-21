import os
import tempfile
import requests
import torch
import torchaudio
from urllib.parse import urlparse
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from pyannote.audio import Pipeline

SUPPORTED_AUDIO_EXT = {".wav", ".mp3"}


class WhisperASR:
    def __init__(self, model_path: str, logger):
        self.logger = logger

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "cuda" else torch.float32

        self.logger.info(f"loading model from {model_path}")
        self.logger.info(f"device={self.device}, dtype={self.dtype}")

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_path,
            torch_dtype=self.dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        ).to(self.device)

        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model.eval()

        # Initialize speaker diarization pipeline
        try:
            self.speaker_pipeline = Pipeline.from_pretrained(os.getenv("DIARIZATION_MODEL_PATH", "pyannote/speaker-diarization-3.1"))
            self.speaker_pipeline.to(torch.device(self.device))
            self.logger.info("speaker diarization pipeline loaded")
        except Exception as e:
            self.logger.warning(f"failed to load speaker diarization pipeline: {e}")
            self.speaker_pipeline = None

        self.logger.info("model loaded")

    def download_audio(self, url: str, trace_id: str) -> str:
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            raise ValueError("invalid url")

        ext = os.path.splitext(url)[1].lower()
        if ext not in SUPPORTED_AUDIO_EXT:
            raise ValueError("unsupported format")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.close()

        headers = {
            "User-Agent": "curl/7.88.1",
            "Accept": "*/*"
        }

        try:
            with requests.get(url, stream=True, timeout=30, headers=headers) as r:
                r.raise_for_status()
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        with open(tmp.name, "ab") as f:
                            f.write(chunk)

            self.logger.info(
                "audio_downloaded",
                extra={
                    "trace_id": trace_id,
                    "audio_url": url
                }
            )
            return tmp.name

        except Exception as e:
            self.logger.exception(
                "audio_download_failed",
                extra={
                    "trace_id": trace_id,
                    "audio_url": url
                }
            )
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
            raise
        except requests.HTTPError as e:
            self.logger.exception(
                "audio_download_http_error",
                extra={
                    "trace_id": trace_id,
                    "audio_url": url,
                    "status_code": e.response.status_code
                }
            )


    def detect_speakers(self, audio_path, trace_id: str):
        """Detect speakers in the audio"""
        if not self.speaker_pipeline:
            self.logger.warning("speaker pipeline not available", extra={"trace_id": trace_id})
            return None

        try:
            # Use pyannote for speaker diarization
            output = self.speaker_pipeline(audio_path)
            diarization = output.speaker_diarization
            
            speakers = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
            
            self.logger.info(
                "speaker detection done",
                extra={"trace_id": trace_id, "speakers": len(speakers)}
            )
            return speakers
        except Exception as e:
            self.logger.exception(
                "speaker detection failed",
                extra={"trace_id": trace_id, "error": str(e)}
            )
            return None

    def assign_speakers_to_segments(self, segments, speakers):
        """Assign speaker information to transcription segments"""
        if not speakers:
            # If no speaker information, assign default speaker to all segments
            for segment in segments:
                segment["speaker"] = "SPEAKER0"
            return segments

        # Create a mapping from original speaker labels to sequential labels
        unique_speakers = list(set([s["speaker"] for s in speakers]))
        speaker_mapping = {original: f"SPEAKER{i}" for i, original in enumerate(unique_speakers)}

        # Assign the most likely speaker to each transcription segment
        for segment in segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            
            # Find the speaker who spoke the most during this time period
            max_overlap = 0
            assigned_speaker = "SPEAKER0"
            
            for speaker_info in speakers:
                speaker_start = speaker_info["start"]
                speaker_end = speaker_info["end"]
                
                # Calculate overlap time
                overlap_start = max(segment_start, speaker_start)
                overlap_end = min(segment_end, speaker_end)
                
                if overlap_start < overlap_end:
                    overlap_duration = overlap_end - overlap_start
                    if overlap_duration > max_overlap:
                        max_overlap = overlap_duration
                        assigned_speaker = speaker_mapping[speaker_info["speaker"]]
            
            segment["speaker"] = assigned_speaker
        
        return segments
        
    def merge_consecutive_speakers(self, segments):
        """Merge consecutive segments from the same speaker"""
        if not segments:
            return segments
            
        merged = []
        current_segment = segments[0].copy()
        
        for i in range(1, len(segments)):
            next_segment = segments[i]
            
            # If same speaker, merge the segments
            if next_segment["speaker"] == current_segment["speaker"]:
                # Extend the end time
                current_segment["end"] = next_segment["end"]
                # Concatenate the text
                current_segment["text"] += " " + next_segment["text"]
            else:
                # Different speaker, save current segment and start new one
                merged.append(current_segment)
                current_segment = next_segment.copy()
        
        # Don't forget the last segment
        merged.append(current_segment)
        
        return merged
        
    def transcribe_segment(self, audio_segment, sr, language):
        """Transcribe a single audio segment"""
        inputs = self.processor(
            audio_segment.squeeze(),
            sampling_rate=sr,
            return_tensors="pt",
            return_attention_mask=True
        ).to(self.device, self.dtype)

        with torch.no_grad():
            ids = self.model.generate(
                **inputs,
                language=language,
                task="transcribe"
            )

        text = self.processor.batch_decode(
            ids,
            skip_special_tokens=True
        )[0].strip()
        
        return text

    def transcribe(self, audio, sr, language, chunk_length, trace_id: str, audio_path: str = None):
        # Preprocess audio
        if audio.shape[0] > 1:
            audio = audio.mean(dim=0, keepdim=True)

        if sr != 16000:
            audio = torchaudio.transforms.Resample(sr, 16000)(audio)
            self.logger.info(
                "resample audio",
                extra={"trace_id": trace_id, "original_sr": sr, "target_sr": 16000}
            )
            sr = 16000

        # If speaker pipeline is not available or audio_path is not provided, fallback to original method
        if not self.speaker_pipeline or not audio_path:
            self.logger.info(
                "speaker pipeline not available or audio_path not provided, using fallback method",
                extra={"trace_id": trace_id, "has_speaker_pipeline": bool(self.speaker_pipeline), "has_audio_path": bool(audio_path)}
            )
            return self._transcribe_fallback(audio, sr, language, chunk_length, trace_id)

        # Perform speaker diarization first
        speakers = self.detect_speakers(audio_path, trace_id)
        if not speakers:
            self.logger.warning(
                "speaker detection failed, using fallback method",
                extra={"trace_id": trace_id}
            )
            return self._transcribe_fallback(audio, sr, language, chunk_length, trace_id)

        # Process each speaker segment
        results = []
        for speaker_info in speakers:
            try:
                # Extract audio segment for this speaker
                start_sample = int(speaker_info["start"] * sr)
                end_sample = int(speaker_info["end"] * sr)
                
                # Ensure boundaries are within audio limits
                start_sample = max(0, start_sample)
                end_sample = min(audio.shape[1], end_sample)
                
                if start_sample >= end_sample:
                    continue
                    
                speaker_audio = audio[:, start_sample:end_sample]
                
                # If segment is too long, split it into smaller chunks
                segment_duration = speaker_info["end"] - speaker_info["start"]
                if segment_duration > chunk_length:
                    # Split long segments into smaller chunks
                    chunk_size = chunk_length * sr
                    for chunk_start in range(0, speaker_audio.shape[1], chunk_size):
                        chunk_end = min(chunk_start + chunk_size, speaker_audio.shape[1])
                        audio_chunk = speaker_audio[:, chunk_start:chunk_end]
                        
                        # Calculate actual time positions
                        chunk_start_time = speaker_info["start"] + chunk_start / sr
                        chunk_end_time = speaker_info["start"] + chunk_end / sr
                        
                        text = self.transcribe_segment(audio_chunk, sr, language)
                        if text:
                            results.append({
                                "start": round(chunk_start_time, 2),
                                "end": round(chunk_end_time, 2),
                                "text": text,
                                "speaker": speaker_info["speaker"]
                            })
                else:
                    # Transcribe the entire segment
                    text = self.transcribe_segment(speaker_audio, sr, language)
                    if text:
                        results.append({
                            "start": round(speaker_info["start"], 2),
                            "end": round(speaker_info["end"], 2),
                            "text": text,
                            "speaker": speaker_info["speaker"]
                        })
            except Exception as e:
                self.logger.exception(
                    "error processing speaker segment",
                    extra={
                        "trace_id": trace_id,
                        "speaker": speaker_info["speaker"],
                        "start": speaker_info["start"],
                        "end": speaker_info["end"],
                        "error": str(e)
                    }
                )
                continue
        
        # Sort results by start time
        results.sort(key=lambda x: x["start"])
        
        # Create sequential speaker labels
        unique_speakers = list(set([s["speaker"] for s in results]))
        speaker_mapping = {original: f"SPEAKER{i}" for i, original in enumerate(sorted(unique_speakers))}
        
        # Apply sequential speaker labels
        for result in results:
            result["speaker"] = speaker_mapping[result["speaker"]]
        
        # Merge consecutive segments from the same speaker
        merged_results = self.merge_consecutive_speakers(results)
        
        self.logger.info(
            "transcribe with speaker diarization done",
            extra={"trace_id": trace_id, "segments": len(merged_results), "speakers": len(unique_speakers)}
        )
        return merged_results

    def _transcribe_fallback(self, audio, sr, language, chunk_length, trace_id: str):
        """Fallback method using original chunking approach"""
        results = []
        chunk_size = chunk_length * sr

        for start in range(0, audio.shape[1], chunk_size):
            end = min(start + chunk_size, audio.shape[1])
            chunk = audio[:, start:end]

            inputs = self.processor(
                chunk.squeeze(),
                sampling_rate=sr,
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.device, self.dtype)

            with torch.no_grad():
                ids = self.model.generate(
                    **inputs,
                    language=language,
                    task="transcribe"
                )

            text = self.processor.batch_decode(
                ids,
                skip_special_tokens=True
            )[0].strip()

            if text:
                results.append({
                    "start": round(start / sr, 2),
                    "end": round(end / sr, 2),
                    "text": text
                })

        # Perform speaker diarization if pipeline is loaded
        # Note: This is less accurate as chunks may span multiple speakers
        speakers = None
        if hasattr(self, 'speaker_pipeline') and self.speaker_pipeline:
            import tempfile
            import torchaudio as ta
            
            # Save temporary audio file for speaker detection
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                ta.save(tmp.name, audio.cpu(), sr)
                speakers = self.detect_speakers(tmp.name, trace_id)
                import os
                os.unlink(tmp.name)
                
            if speakers:
                results = self.assign_speakers_to_segments(results, speakers)

        self.logger.info(
            "transcribe fallback done",
            extra={"trace_id": trace_id, "segments": len(results)}
        )
        return results
