"""
Audio processing utilities for meeting recordings.
Preserves and enhances the existing Whisper.cpp functionality.
"""

import os
import subprocess
import tempfile
from typing import Tuple, Optional
from pathlib import Path
import ffmpeg
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Audio processing utilities for meeting recordings."""
    
    def __init__(self):
        self.logger = logger
        self.whisper_model_dir = Path(settings.WHISPER_MODEL_DIR)
        self.temp_dir = Path(tempfile.gettempdir()) / "meeting_summarizer"
        self.temp_dir.mkdir(exist_ok=True)
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Validate if the audio file is supported."""
        try:
            file_ext = Path(file_path).suffix.lower()
            return file_ext in settings.ALLOWED_AUDIO_FORMATS
        except Exception as e:
            self.logger.error(f"Error validating audio file: {e}")
            return False
    
    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """Get audio file duration in seconds."""
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            self.logger.error(f"Error getting audio duration: {e}")
            return None
    
    def get_audio_info(self, file_path: str) -> dict:
        """Get comprehensive audio file information."""
        try:
            probe = ffmpeg.probe(file_path)
            audio_stream = probe['streams'][0]
            
            return {
                'duration': float(audio_stream.get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bit_rate': int(audio_stream.get('bit_rate', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'format': probe['format'].get('format_name', 'unknown')
            }
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            return {}
    
    def preprocess_audio_file(self, input_path: str) -> Tuple[str, bool]:
        """
        Preprocess audio file for optimal Whisper performance.
        Returns: (output_path, success)
        
        Preserves the original preprocessing logic while adding improvements.
        """
        try:
            input_file = Path(input_path)
            
            # Generate unique output filename
            output_file = self.temp_dir / f"{input_file.stem}_processed_{os.getpid()}.wav"
            
            self.logger.info(f"Preprocessing audio file: {input_path}")
            
            # Use ffmpeg-python for more robust processing
            stream = ffmpeg.input(input_path)
            
            # Convert to optimal format for Whisper:
            # - 16kHz sample rate
            # - Mono channel
            # - WAV format
            stream = ffmpeg.output(
                stream,
                str(output_file),
                acodec='pcm_s16le',  # 16-bit PCM
                ar=16000,            # 16kHz sample rate
                ac=1,                # Mono
                y=None               # Overwrite existing file
            )
            
            # Run the conversion
            ffmpeg.run(stream, quiet=True, overwrite_output=True)
            
            self.logger.info(f"Audio preprocessing completed: {output_file}")
            return str(output_file), True
            
        except Exception as e:
            self.logger.error(f"Error preprocessing audio file: {e}")
            return input_path, False
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary files."""
        try:
            if os.path.exists(file_path) and self.temp_dir.name in file_path:
                os.remove(file_path)
                self.logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp file {file_path}: {e}")
    
    def get_available_whisper_models(self) -> list[str]:
        """
        Get available Whisper models from the whisper.cpp/models directory.
        Preserves the original model discovery logic.
        """
        try:
            if not self.whisper_model_dir.exists():
                self.logger.warning(f"Whisper model directory not found: {self.whisper_model_dir}")
                return []
            
            # List of acceptable official Whisper models
            valid_models = ["base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]
            
            # Get the list of model files in the models directory
            model_files = [f.name for f in self.whisper_model_dir.glob("*.bin")]
            
            # Filter out test models and models that aren't in the valid list
            whisper_models = []
            for model_file in model_files:
                # Remove the .bin extension and ggml- prefix
                model_name = model_file.replace('.bin', '').replace('ggml-', '')
                
                # Check if it's a valid model and not a test model
                if any(valid_model in model_name for valid_model in valid_models) and "test" not in model_name:
                    whisper_models.append(model_name)
            
            # Remove duplicates and sort
            whisper_models = sorted(list(set(whisper_models)))
            
            self.logger.info(f"Found Whisper models: {whisper_models}")
            return whisper_models
            
        except Exception as e:
            self.logger.error(f"Error getting available Whisper models: {e}")
            return []
    
    def transcribe_with_whisper_cpp(
        self, 
        audio_path: str, 
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Tuple[str, bool, Optional[float], list[dict]]:
        """
        Transcribe audio using whisper.cpp.
        Preserves the original transcription logic with improvements.
        
        Returns: (transcript, success, confidence_score, segments)
        """
        try:
            # Validate model availability
            available_models = self.get_available_whisper_models()
            if model_name not in available_models:
                self.logger.error(f"Model {model_name} not available. Available: {available_models}")
                return "", False, None, []
            
            model_path = self.whisper_model_dir / f"ggml-{model_name}.bin"
            if not model_path.exists():
                self.logger.error(f"Model file not found: {model_path}")
                return "", False, None, []
            
            # Preprocess audio
            processed_audio, preprocessing_success = self.preprocess_audio_file(audio_path)
            if not preprocessing_success:
                self.logger.warning("Audio preprocessing failed, using original file")
                processed_audio = audio_path
            
            # Create temporary output file
            output_file = self.temp_dir / f"transcript_{os.getpid()}.txt"
            
            # Build whisper.cpp command
            whisper_binary = Path("./whisper.cpp/main")
            if os.name == 'nt':  # Windows
                whisper_binary = Path("./whisper.cpp/main.exe")
            
            cmd = [
                str(whisper_binary),
                "-m", str(model_path),
                "-f", processed_audio,
                "-otxt",  # Output as text
                "-osrt"   # Output as SRT for segments
            ]
            
            # Add language parameter if specified
            if language:
                cmd.extend(["-l", language])
            
            self.logger.info(f"Starting Whisper.cpp transcription with command: {' '.join(cmd)}")
            
            # Run whisper.cpp
            result = subprocess.run(
                cmd,
                cwd=".",
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"Whisper.cpp failed with return code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")
                return "", False, None, []
            
            # Read the transcript from the generated text file
            # Whisper.cpp generates filename.wav.txt
            transcript_file = Path(processed_audio + ".txt")
            srt_file = Path(processed_audio + ".srt")
            
            segments = []
            if srt_file.exists():
                try:
                    import re
                    with open(srt_file, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                    
                    # Parse SRT blocks
                    blocks = re.split(r'\n\s*\n', srt_content.strip())
                    for block in blocks:
                        lines = block.strip().split('\n')
                        if len(lines) >= 3:
                            time_match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})', lines[1])
                            if time_match:
                                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, time_match.groups())
                                start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                                end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                                text = " ".join(lines[2:]).strip()
                                segments.append({
                                    'start': start_sec,
                                    'end': end_sec,
                                    'text': text,
                                    'confidence': 0.8
                                })
                except Exception as ex:
                    self.logger.error(f"Error parsing whisper.cpp srt output: {ex}")
                finally:
                    if srt_file.exists():
                        srt_file.unlink()
            
            if transcript_file.exists():
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
                
                # Clean up transcript file
                transcript_file.unlink()
                
                # Clean up processed audio file if it was temporary
                if processed_audio != audio_path:
                    self.cleanup_temp_file(processed_audio)
                
                self.logger.info("Whisper.cpp transcription completed successfully")
                
                # Calculate a basic confidence score based on transcript length and quality
                confidence_score = self._calculate_confidence_score(transcript)
                
                return transcript, True, confidence_score, segments
            else:
                self.logger.error(f"Transcript file not found: {transcript_file}")
                return "", False, None, []
                
        except subprocess.TimeoutExpired:
            self.logger.error("Whisper.cpp transcription timed out")
            return "", False, None, []
        except Exception as e:
            self.logger.error(f"Error in Whisper.cpp transcription: {e}")
            return "", False, None, []
    
    def _calculate_confidence_score(self, transcript: str) -> float:
        """Calculate a basic confidence score based on transcript characteristics."""
        if not transcript:
            return 0.0
        
        # Basic heuristics for confidence scoring
        words = transcript.split()
        word_count = len(words)
        
        # Factors that increase confidence
        confidence = 0.5  # Base confidence
        
        # More words generally indicate better transcription
        if word_count > 10:
            confidence += 0.1
        if word_count > 50:
            confidence += 0.1
        if word_count > 100:
            confidence += 0.1
        
        # Presence of punctuation indicates better quality
        punctuation_count = sum(1 for char in transcript if char in '.,!?;:')
        if punctuation_count > 0:
            confidence += min(0.1, punctuation_count / word_count)
        
        # Absence of obvious transcription errors
        error_indicators = ['[BLANK_AUDIO]', '[NOISE]', '***', '???']
        has_errors = any(error in transcript for error in error_indicators)
        if has_errors:
            confidence -= 0.2
        
        # Clamp confidence between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def extract_audio_segment(
        self, 
        input_path: str, 
        start_time: float, 
        end_time: float
    ) -> Tuple[str, bool]:
        """Extract a segment of audio file."""
        try:
            input_file = Path(input_path)
            output_file = self.temp_dir / f"{input_file.stem}_segment_{start_time}_{end_time}.wav"
            
            stream = ffmpeg.input(input_path, ss=start_time, t=(end_time - start_time))
            stream = ffmpeg.output(stream, str(output_file))
            ffmpeg.run(stream, quiet=True, overwrite_output=True)
            
            return str(output_file), True
        except Exception as e:
            self.logger.error(f"Error extracting audio segment: {e}")
            return "", False


# Create global instance
audio_processor = AudioProcessor()