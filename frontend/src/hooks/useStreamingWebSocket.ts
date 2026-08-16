import { useState, useEffect, useRef, useCallback } from 'react';

interface StreamingWebSocketMessage {
  type: string;
  text?: string;
  message?: string;
  [key: string]: any;
}

export const useStreamingWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Not connected');
  const [transcript, setTranscript] = useState('');
  const [responseText, setResponseText] = useState('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(url);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        setStatus('Connected');
        // Initialize audio context for streaming playback
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      };
      
      wsRef.current.onmessage = async (event: MessageEvent) => {
        if (event.data instanceof Blob) {
          // Audio chunk - play it immediately for streaming
          console.log('Received audio chunk, size:', event.data.size);
          await playAudioChunk(event.data);
        } else {
          // JSON message
          try {
            const msg: StreamingWebSocketMessage = JSON.parse(event.data);
            console.log('Message:', msg);
            
            if (msg.type === 'error') {
              setStatus(`Error: ${msg.message}`);
            } else if (msg.type === 'transcript') {
              setTranscript(msg.text || '');
              setStatus('Transcribing...');
            } else if (msg.type === 'response_chunk') {
              setResponseText(prev => prev + (msg.text || ''));
              setStatus('AI responding...');
            } else if (msg.type === 'stream_complete') {
              setStatus('Complete');
            }
          } catch (e) {
            console.error('Failed to parse message:', e);
          }
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('Error: Connection failed');
        setIsConnected(false);
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        setStatus('Disconnected');
      };
    } catch (error) {
      console.error('Failed to connect:', error);
      setStatus('Error: Failed to connect');
    }
  }, [url]);

  const playAudioChunk = async (chunk: Blob) => {
    if (!audioContextRef.current) return;
    
    try {
      const arrayBuffer = await chunk.arrayBuffer();
      const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start();
      
      setStatus('Playing audio...');
    } catch (e) {
      console.error('Error playing audio chunk:', e);
    }
  };

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setIsConnected(false);
    setStatus('Disconnected');
  }, []);

  const sendBytes = useCallback((data: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const sendJson = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const startRecording = useCallback(() => {
    sendJson({ type: 'start_recording' });
    setStatus('Listening...');
  }, [sendJson]);

  const stopRecording = useCallback(() => {
    sendJson({ type: 'stop_recording' });
    setStatus('Processing...');
  }, [sendJson]);

  const interrupt = useCallback(() => {
    sendJson({ type: 'interrupt' });
    setStatus('Interrupting...');
  }, [sendJson]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    status,
    transcript,
    responseText,
    audioPlayerRef,
    connect,
    disconnect,
    sendBytes,
    sendJson,
    startRecording,
    stopRecording,
    interrupt,
  };
};