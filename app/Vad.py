import webrtcvad
import collections
import numpy as np

class VoiceActivityDetector:
    """Real-time voice activity detection using WebRTC VAD."""
    
    def __init__(self, aggressiveness=3, sample_rate=16000, frame_duration_ms=30):
        """
        Args:
            aggressiveness: 0-3, higher = more aggressive filtering
            sample_rate: Audio sample rate (default 16000 for Whisper)
            frame_duration_ms: Frame duration in ms (10, 20, or 30)
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000) * 2  # 16-bit samples
        
        # State tracking
        self.speech_frames = 0
        self.silence_frames = 0
        self.speech_threshold = 10  # Frames to confirm speech started
        self.silence_threshold = 20  # Frames of silence to end speech
        
    def is_speech(self, frame_bytes):
        """Check if a frame contains speech."""
        if len(frame_bytes) < self.frame_size:
            return False
        return self.vad.is_speech(frame_bytes, self.sample_rate)
    
    def process_frame(self, frame_bytes):
        """
        Process a single audio frame.
        Returns: "speech", "silence", or "speech_ended"
        """
        is_speech = self.is_speech(frame_bytes)
        
        if is_speech:
            self.speech_frames += 1
            self.silence_frames = 0
            
            if self.speech_frames >= self.speech_threshold:
                return "speech"
        else:
            self.silence_frames += 1
            
            if self.speech_frames >= self.speech_threshold:
                if self.silence_frames >= self.silence_threshold:
                    self.speech_frames = 0
                    self.silence_frames = 0
                    return "speech_ended"
        
        return "silence"
    
    def reset(self):
        """Reset VAD state."""
        self.speech_frames = 0
        self.silence_frames = 0