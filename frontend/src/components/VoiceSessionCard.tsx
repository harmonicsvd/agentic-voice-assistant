import { useState, useEffect } from 'react';
import { PipecatClient, RTVIEvent } from '@pipecat-ai/client-js';
import { VoiceEmoji } from './motion/VoiceEmoji';
import { UI_CONFIG, CharacterState } from '../config/ui-config';

interface VoiceSessionCardProps {
  userSub: string;
  client: PipecatClient;
  onColorChange?: (color: string) => void;
}

interface Meeting {
  title: string;
  name: string;
  date: string;
  time: string;
}

export const VoiceSessionCard = ({ userSub, client, onColorChange }: VoiceSessionCardProps) => {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [status, setStatus] = useState('Sleeping');
  const [btnLabel, setBtnLabel] = useState(UI_CONFIG.voiceSession.buttonLabels.startCall);
  const [btnHint, setBtnHint] = useState(UI_CONFIG.voiceSession.buttonHints.idle);
  
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [botReady, setBotReady] = useState(false);
  const [isFirstResponse, setIsFirstResponse] = useState(true); // Track first response
  const [hasWokenUp, setHasWokenUp] = useState(false); // Track if bot has woken up once

  const [jerryState, setJerryState] = useState<CharacterState>('idle');

  // Connect Pipecat events to character state
  useEffect(() => {
    if (!client) return;

    const handleUserStartedSpeaking = () => {
      if (isRecording && botReady) {
        setJerryState('listening'); // User speaks → listening
        setStatus('Listening');
      }
    };
    const handleUserStoppedSpeaking = () => {
      if (isRecording && botReady) {
        setJerryState('thinking'); // User stops → thinking
        setStatus('Thinking');
      }
    };
    const handleBotLlmStarted = () => {
      if (isRecording && botReady) {
        setJerryState('processing'); // Bot searching → processing
        setStatus('Processing');
      }
    };
    const handleFunctionCallStarted = () => {
      if (isRecording && botReady) {
        setJerryState('processing'); // Function call → processing
        setStatus('Processing');
      }
    };
    const handleBotTtsStarted = () => {
      if (isRecording && botReady) {
        setJerryState('processing'); // Show processing while TTS generates
        setStatus('Processing');
      }
    };
    const handleBotStartedSpeaking = () => {
      if (isRecording && botReady) {
        setJerryState('speaking'); // Bot speaks → speaking (when audio actually plays)
        setStatus('Speaking');
        setIsFirstResponse(false); // Reset after first response
      }
    };
    const handleBotStoppedSpeaking = () => {
      if (isRecording && botReady) {
        setJerryState('listening'); // Bot stops → listening (waiting for user)
        setStatus('Listening');
      }
    };
    const handleBotReady = () => {
      setBotReady(true);
      if (!hasWokenUp) {
        setJerryState('success'); // Bot ready → ready (only on first wake up)
        setStatus('Ready');
        setHasWokenUp(true);
      } else {
        setJerryState('listening'); // After first wake up, go to listening
        setStatus('Listening');
      }
    };
    const handleBotDisconnected = () => {
      setBotReady(false);
      setHasWokenUp(false); // Reset wake up flag
      setJerryState('idle'); // Bot disconnected → sleeping
      setStatus('Sleeping');
    };
    const handleError = () => {
      setJerryState('error');
      setStatus('Error');
    };

    client.on(RTVIEvent.UserStartedSpeaking, handleUserStartedSpeaking);
    client.on(RTVIEvent.UserStoppedSpeaking, handleUserStoppedSpeaking);
    client.on(RTVIEvent.BotLlmStarted, handleBotLlmStarted);
    client.on(RTVIEvent.LLMFunctionCallStarted, handleFunctionCallStarted);
    client.on(RTVIEvent.BotTtsStarted, handleBotTtsStarted);
    client.on(RTVIEvent.BotStartedSpeaking, handleBotStartedSpeaking);
    client.on(RTVIEvent.BotStoppedSpeaking, handleBotStoppedSpeaking);
    client.on(RTVIEvent.BotReady, handleBotReady);
    client.on(RTVIEvent.BotDisconnected, handleBotDisconnected);
    client.on(RTVIEvent.Error, handleError);

    return () => {
      client.off(RTVIEvent.UserStartedSpeaking, handleUserStartedSpeaking);
      client.off(RTVIEvent.UserStoppedSpeaking, handleUserStoppedSpeaking);
      client.off(RTVIEvent.BotLlmStarted, handleBotLlmStarted);
      client.off(RTVIEvent.LLMFunctionCallStarted, handleFunctionCallStarted);
      client.off(RTVIEvent.BotTtsStarted, handleBotTtsStarted);
      client.off(RTVIEvent.BotStartedSpeaking, handleBotStartedSpeaking);
      client.off(RTVIEvent.BotStoppedSpeaking, handleBotStoppedSpeaking);
      client.off(RTVIEvent.BotReady, handleBotReady);
      client.off(RTVIEvent.BotDisconnected, handleBotDisconnected);
      client.off(RTVIEvent.Error, handleError);
    };
  }, [client, isRecording, botReady, hasWokenUp]);

  const toggleRecording = async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  };

  const startRecording = async () => {
    try {
      setIsLoading(true);
      setStatus('Waking up');
      setJerryState('idle'); // Show sleepy face when turning on (until agent speaks)
      setIsFirstResponse(true); // Reset first response flag
      setHasWokenUp(false); // Reset wake up flag

      if (!client) {
        setStatus('Error');
        setJerryState('error');
        return;
      }

      await client.connect();

      setIsConnected(true);
      setIsRecording(true);
      setBtnLabel(UI_CONFIG.voiceSession.buttonLabels.endCall);
      setBtnHint(UI_CONFIG.voiceSession.buttonHints.listening);
      setStatus('Listening');
      setJerryState('listening');
    } catch (err) {
      console.error(err);
      setStatus('Error');
      setJerryState('error');
    } finally {
      setIsLoading(false);
    }
  };

  const stopRecording = async () => {
    try {
      if (!client) return;

      setBotReady(false);
      setJerryState('idle');
      setStatus('Sleeping');
      await client.disconnect();
      setIsConnected(false);
      setIsRecording(false);
      setBtnLabel(UI_CONFIG.voiceSession.buttonLabels.startCall);
      setBtnHint(UI_CONFIG.voiceSession.buttonHints.disconnected);
    } catch (err) {
      console.error(err);
    }
  };

  const addMeeting = (result: string) => {
    const titleMatch = result.match(/['"](.+?)['"]/);
    const dateMatch = result.match(/on (\d{4}-\d{2}-\d{2})/);
    const timeMatch = result.match(/at (\d{2}:\d{2})/);
    const nameMatch = result.match(/for (.+?) on/);

    const newMeeting: Meeting = {
      title: titleMatch ? titleMatch[1] : 'Meeting',
      date: dateMatch ? dateMatch[1] : '',
      time: timeMatch ? timeMatch[1] : '',
      name: nameMatch ? nameMatch[1] : 'Guest',
    };

    setMeetings((prev) => [newMeeting, ...prev].slice(0, 5));
  };

  const transcript = '';
  const responseText = '';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '32px',
      width: '100%',
      maxWidth: '600px',
    }}>
      {/* Emoji Character */}
      <div className="lottie-character" style={{width: '200px', height: '200px'}}>
        <VoiceEmoji state={jerryState} onColorChange={onColorChange} />
      </div>

      {/* Status Text */}
      <p style={{
        fontSize: '1.25rem',
        color: UI_CONFIG.colors.secondary,
        textAlign: 'center',
        minHeight: '24px',
      }}>
        {status || (jerryState === 'error' ? 'Error' : '')}
      </p>

      {/* Microphone Button */}
      <div 
        onClick={toggleRecording}
        style={{
          position: 'relative',
          width: '100px',
          height: '100px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
        }}
      >
        {/* Animated Rings */}
        <div style={{
          position: 'absolute',
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          border: '2px solid rgba(14, 165, 233, 0.3)',
          opacity: isRecording ? 0.6 : 0,
          animation: isRecording ? `pulse ${UI_CONFIG.animation.pulseDuration} ease-out infinite` : 'none',
        }}></div>
        <div style={{
          position: 'absolute',
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          border: '2px solid rgba(14, 165, 233, 0.4)',
          opacity: isRecording ? 0.5 : 0,
          animation: isRecording ? `pulse ${UI_CONFIG.animation.pulseDuration} ease-out infinite ${UI_CONFIG.animation.pulseDelay}` : 'none',
        }}></div>
        <div style={{
          position: 'absolute',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          border: '2px solid rgba(14, 165, 233, 0.5)',
          opacity: isRecording ? 0.4 : 0,
          animation: isRecording ? `pulse ${UI_CONFIG.animation.pulseDuration} ease-out infinite 0.6s` : 'none',
        }}></div>

        {/* Main Button */}
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: isRecording ? UI_CONFIG.colors.primary : 'white',
          border: '3px solid white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 4px 20px ${UI_CONFIG.colors.primary}40`,
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          opacity: isLoading ? 0.5 : 1,
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={isRecording ? 'white' : '#0ea5e9'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="22"/>
          </svg>
        </div>
      </div>
    </div>
  );
};
