import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState('Not connected');
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [bufferSize, setBufferSize] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const connect = useCallback(() => {
    try {
      wsRef.current = new WebSocket(url);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        setStatus('Connected');
      };
      
      wsRef.current.onmessage = async (event: MessageEvent) => {
        if (event.data instanceof Blob) {
          // Audio chunk - buffer it
          audioChunksRef.current.push(event.data);
          console.log(`Received audio chunk ${audioChunksRef.current.length}, size: ${event.data.size}`);
          setStatus(`Received audio chunk ${audioChunksRef.current.length}`);
        } else {
          // JSON message
          try {
            const msg: WebSocketMessage = JSON.parse(event.data);
            console.log('Message:', msg);
            
            if (msg.type === 'error') {
              setStatus(`Error: ${msg.error}`);
              audioChunksRef.current = [];
            } else if (msg.type === 'chunk_received') {
              setBufferSize(msg.buffer_size || 0);
              setStatus(`Buffer: ${msg.buffer_size} chunks`);
            } else if (msg.type === 'audio_complete') {
              // Stream complete, play audio
              console.log('Audio stream complete, playing audio');
              console.log(`Total chunks: ${audioChunksRef.current.length}`);
              
              if (audioChunksRef.current.length > 0) {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                console.log(`Audio blob size: ${audioBlob.size} bytes`);
                const url = URL.createObjectURL(audioBlob);
                console.log(`Audio URL: ${url}`);
                setAudioUrl(url);
                setStatus('Playing response');
                audioChunksRef.current = [];
              } else {
                console.error('No audio chunks to play');
              }
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

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
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

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    status,
    audioUrl,
    bufferSize,
    audioPlayerRef,
    connect,
    disconnect,
    sendBytes,
    sendJson,
  };
};
