"""
Speaker diarization service using pyannote.audio.
"""

import os
import tempfile
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.audio_processor import audio_processor

logger = get_logger(__name__)


class SpeakerDiarizationService:
    """
    Service for speaker diarization using pyannote.audio.
    """
    
    def __init__(self):
        self.logger = logger
        self.pipeline = None
        self.huggingface_token = settings.HUGGINGFACE_TOKEN
        
    async def initialize_pipeline(self) -> bool:
        """Initialize the diarization pipeline."""
        try:
            import torch
            from pyannote.audio import Pipeline
            if self.pipeline is not None:
                return True
                
            if not self.huggingface_token:
                self.logger.warning("HuggingFace token not configured, speaker diarization unavailable")
                return False
            
            self.logger.info("Initializing speaker diarization pipeline...")
            
            # Load pipeline in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.pipeline = await loop.run_in_executor(
                None,
                lambda: Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.huggingface_token
                )
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
                self.logger.info("Speaker diarization pipeline loaded on GPU")
            else:
                self.logger.info("Speaker diarization pipeline loaded on CPU")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speaker diarization pipeline: {e}")
            return False
    
    async def diarize_audio(
        self, 
        audio_path: str,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict:
        """
        Perform speaker diarization on audio file.
        
        Returns:
            {
                'segments': List[Dict],  # Speaker segments with timing
                'num_speakers': int,     # Total number of speakers
                'speakers': List[str],   # List of speaker labels
                'success': bool
            }
        """
        try:
            # Initialize pipeline if not already done
            if not await self.initialize_pipeline():
                return {
                    'segments': [],
                    'num_speakers': 0,
                    'speakers': [],
                    'success': False,
                    'error': 'Pipeline initialization failed'
                }
            
            self.logger.info(f"Starting speaker diarization for: {audio_path}")
            
            # Preprocess audio for optimal diarization
            processed_audio, success = audio_processor.preprocess_audio_file(audio_path)
            if not success:
                processed_audio = audio_path
            
            # Prepare diarization parameters
            diarization_params = {}
            if min_speakers is not None:
                diarization_params['min_speakers'] = min_speakers
            if max_speakers is not None:
                diarization_params['max_speakers'] = max_speakers
            
            # Run diarization in thread pool
            loop = asyncio.get_event_loop()
            
            # Create progress hook for monitoring
            from pyannote.audio.pipelines.utils.hook import ProgressHook
            with ProgressHook() as hook:
                diarization = await loop.run_in_executor(
                    None,
                    lambda: self.pipeline(processed_audio, hook=hook, **diarization_params)
                )
            
            # Process diarization results
            segments = []
            speakers = set()
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start_time': turn.start,
                    'end_time': turn.end,
                    'duration': turn.end - turn.start,
                    'speaker_id': speaker,
                    'speaker_label': self._generate_speaker_label(speaker)
                })
                speakers.add(speaker)
            
            # Sort segments by start time
            segments.sort(key=lambda x: x['start_time'])
            
            # Clean up processed file if it was temporary
            if processed_audio != audio_path:
                audio_processor.cleanup_temp_file(processed_audio)
            
            result = {
                'segments': segments,
                'num_speakers': len(speakers),
                'speakers': sorted(list(speakers)),
                'success': True
            }
            
            self.logger.info(
                f"Speaker diarization completed. Found {len(speakers)} speakers "
                f"in {len(segments)} segments"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Speaker diarization failed: {e}")
            return {
                'segments': [],
                'num_speakers': 0,
                'speakers': [],
                'success': False,
                'error': str(e)
            }
    
    async def diarize_and_align_with_transcript(
        self,
        audio_path: str,
        transcript_segments: List[Dict],
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict:
        """
        Perform speaker diarization and align with transcript segments.
        
        Args:
            transcript_segments: List of transcript segments with 'start', 'end', 'text'
            
        Returns:
            {
                'aligned_segments': List[Dict],  # Transcript segments with speaker info
                'speaker_segments': List[Dict],  # Pure speaker segments
                'num_speakers': int,
                'speakers': List[str],
                'success': bool
            }
        """
        try:
            # First, get speaker diarization
            diarization_result = await self.diarize_audio(
                audio_path, min_speakers, max_speakers
            )
            
            if not diarization_result['success']:
                return diarization_result
            
            speaker_segments = diarization_result['segments']
            
            # Align transcript segments with speaker segments
            aligned_segments = []
            
            for transcript_segment in transcript_segments:
                t_start = transcript_segment.get('start', 0)
                t_end = transcript_segment.get('end', 0)
                t_text = transcript_segment.get('text', '')
                
                # Find overlapping speaker segments
                overlapping_speakers = []
                max_overlap = 0
                primary_speaker = "SPEAKER_UNKNOWN"
                
                for speaker_segment in speaker_segments:
                    s_start = speaker_segment['start_time']
                    s_end = speaker_segment['end_time']
                    
                    # Calculate overlap
                    overlap_start = max(t_start, s_start)
                    overlap_end = min(t_end, s_end)
                    overlap_duration = max(0, overlap_end - overlap_start)
                    
                    if overlap_duration > 0:
                        overlapping_speakers.append({
                            'speaker_id': speaker_segment['speaker_id'],
                            'speaker_label': speaker_segment['speaker_label'],
                            'overlap_duration': overlap_duration
                        })
                        
                        # Track primary speaker (with most overlap)
                        if overlap_duration > max_overlap:
                            max_overlap = overlap_duration
                            primary_speaker = speaker_segment['speaker_label']
                
                aligned_segments.append({
                    'start_time': t_start,
                    'end_time': t_end,
                    'duration': t_end - t_start,
                    'text': t_text,
                    'primary_speaker': primary_speaker,
                    'overlapping_speakers': overlapping_speakers,
                    'confidence': transcript_segment.get('confidence', 0.0)
                })
            
            return {
                'aligned_segments': aligned_segments,
                'speaker_segments': speaker_segments,
                'num_speakers': diarization_result['num_speakers'],
                'speakers': diarization_result['speakers'],
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Speaker diarization and alignment failed: {e}")
            return {
                'aligned_segments': [],
                'speaker_segments': [],
                'num_speakers': 0,
                'speakers': [],
                'success': False,
                'error': str(e)
            }
    
    def _generate_speaker_label(self, speaker_id: str) -> str:
        """Generate human-readable speaker label."""
        # Extract speaker number from pyannote speaker ID (e.g., "SPEAKER_00" -> "Speaker 1")
        try:
            if "SPEAKER_" in speaker_id:
                speaker_num = int(speaker_id.split("_")[-1]) + 1
                return f"Speaker {speaker_num}"
            else:
                return speaker_id
        except:
            return speaker_id
    
    def format_transcript_with_speakers(
        self, 
        aligned_segments: List[Dict],
        include_timestamps: bool = True
    ) -> str:
        """Format transcript with speaker labels."""
        try:
            formatted_lines = []
            current_speaker = None
            current_text_parts = []
            
            for segment in aligned_segments:
                speaker = segment['primary_speaker']
                text = segment['text'].strip()
                
                if not text:
                    continue
                
                # If speaker changes, output previous speaker's text
                if current_speaker != speaker:
                    if current_speaker and current_text_parts:
                        speaker_text = " ".join(current_text_parts)
                        if include_timestamps:
                            formatted_lines.append(f"\n{current_speaker}: {speaker_text}")
                        else:
                            formatted_lines.append(f"{current_speaker}: {speaker_text}")
                    
                    current_speaker = speaker
                    current_text_parts = [text]
                else:
                    current_text_parts.append(text)
            
            # Add the last speaker's text
            if current_speaker and current_text_parts:
                speaker_text = " ".join(current_text_parts)
                if include_timestamps:
                    formatted_lines.append(f"\n{current_speaker}: {speaker_text}")
                else:
                    formatted_lines.append(f"{current_speaker}: {speaker_text}")
            
            return "\n".join(formatted_lines).strip()
            
        except Exception as e:
            self.logger.error(f"Error formatting transcript with speakers: {e}")
            return ""
    
    def get_speaker_statistics(self, speaker_segments: List[Dict]) -> Dict[str, Any]:
        """Get statistics about speakers in the meeting."""
        try:
            if not speaker_segments:
                return {}
            
            speaker_stats = {}
            total_duration = 0
            
            # Calculate speaking time per speaker
            for segment in speaker_segments:
                speaker = segment['speaker_label']
                duration = segment['duration']
                total_duration += duration
                
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        'total_time': 0,
                        'segment_count': 0,
                        'avg_segment_length': 0,
                        'percentage': 0
                    }
                
                speaker_stats[speaker]['total_time'] += duration
                speaker_stats[speaker]['segment_count'] += 1
            
            # Calculate percentages and averages
            for speaker, stats in speaker_stats.items():
                if total_duration > 0:
                    stats['percentage'] = (stats['total_time'] / total_duration) * 100
                
                if stats['segment_count'] > 0:
                    stats['avg_segment_length'] = stats['total_time'] / stats['segment_count']
            
            # Sort by speaking time
            sorted_stats = dict(
                sorted(speaker_stats.items(), 
                      key=lambda x: x[1]['total_time'], 
                      reverse=True)
            )
            
            return {
                'speaker_statistics': sorted_stats,
                'total_duration': total_duration,
                'num_speakers': len(speaker_stats),
                'most_active_speaker': next(iter(sorted_stats)) if sorted_stats else None
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating speaker statistics: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if speaker diarization is available."""
        return bool(self.huggingface_token)


# Create global service instance
speaker_diarization_service = SpeakerDiarizationService()