import { useState, useEffect } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { WebSocketTransport, ProtobufFrameSerializer } from '@pipecat-ai/websocket-transport';
import { BrandBar } from './BrandBar';
import { StorySection } from './StorySection';
import { VoiceSessionCard } from './VoiceSessionCard';
import { CalendarBackground } from './CalendarBackground';

// Create Pipecat client instance with serializer for WebSocket compatibility
const client = new PipecatClient({
  transport: new WebSocketTransport({
    wsUrl: 'ws://localhost:8000/ws/pipecat',
    serializer: new ProtobufFrameSerializer(),
    recorderSampleRate: 16000,
    playerSampleRate: 24000,
  }),
  enableMic: true,
  enableCam: false,
}) as any;

export const VoiceAssistant = () => {
  const [userSub, setUserSub] = useState('');

  useEffect(() => {
    // Get user sub from auth
    const fetchUser = async () => {
      try {
        const res = await fetch('/auth/me', { credentials: 'include' });
        if (res.status === 200) {
          const me = await res.json();
          setUserSub(me.user?.sub || '');
        }
      } catch (e) {
        console.error('Auth check failed', e);
      }
    };

    fetchUser();
  }, []);


  return (
    <>
      <CalendarBackground />
      <div className="page">
        <BrandBar userSub={userSub} />
        <div className="shell">
          <StorySection />
          <VoiceSessionCard userSub={userSub} client={client} />
        </div>
      </div>
    </>
  );
};
