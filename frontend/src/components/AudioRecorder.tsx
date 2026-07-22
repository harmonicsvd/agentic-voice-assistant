import { useState, useRef, useCallback } from 'react';

interface AudioRecorderProps {
  onChunk: (chunk: ArrayBuffer) => void;
  onComplete: (completeFile: Blob) => void;
  disabled?: boolean;
}

export const AudioRecorder = ({ onChunk, onComplete, disabled }: AudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          event.data.arrayBuffer().then((buffer) => {
            onChunk(buffer);
          });
        }
      };
      
      mediaRecorder.start(100);
      setIsRecording(true);
      setError(null);
    } catch (err) {
      console.error('Microphone access denied:', err);
      setError('Microphone access denied. Please allow microphone permission.');
      alert('Microphone access is required. Please allow microphone access in your browser settings.');
    }
  }, [onChunk]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsRecording(false);
    
    // Send complete file
    const completeBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
    onComplete(completeBlob);
    chunksRef.current = [];
  }, [onComplete]);

  return (
    <div>
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        style={{
          padding: '10px 20px',
          margin: '5px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.5 : 1,
        }}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
      {error && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}
    </div>
  );
};