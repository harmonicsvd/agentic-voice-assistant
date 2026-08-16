import { useState, useEffect } from 'react';
import { PipecatClient, RTVIEvent } from '@pipecat-ai/client-js';

import { VoiceEmoji } from './motion/VoiceEmoji';
import { CharacterState } from '../config/ui-config';



interface VoiceSessionCardProps {
  userSub: string;
  client: PipecatClient;
  sleepStatus?: string;
}
export const VoiceSessionCard = ({ userSub: _userSub, client, sleepStatus }: VoiceSessionCardProps) => {
  const [status, setStatus] = useState('Ready'); // Start with Ready status
  const [isMicActive, setIsMicActive] = useState(false); // Visual state for mic button
  const [isLoading, setIsLoading] = useState(false);
  const [hasWokenUp, setHasWokenUp] = useState(false); // Track if bot has woken up once
  const [hasShownReady, setHasShownReady] = useState(true); // Ready state shown initially
  const [lastUserActivity, setLastUserActivity] = useState<number>(Date.now()); // Track last user activity
  const [lastBotSpeechEnd, setLastBotSpeechEnd] = useState<number | null>(null); // Track when bot last stopped speaking
  const [isConnected, setIsConnected] = useState(false); // Track if WebSocket is connected

  const [jerryState, setJerryState] = useState<CharacterState>('success'); // Start with smile emoji
  const [isWakingUp, setIsWakingUp] = useState(false); // Track if we're in wake-up transition

  // Sync status with backend sleep state updates
  useEffect(() => {
    if (sleepStatus) {
      console.log('🔄 Syncing status with backend sleepStatus:', sleepStatus, 'current status:', status);
      
      // Handle sleeping state
      if (sleepStatus === 'Sleeping') {
        setStatus('Sleeping');
        setJerryState('idle');
        setIsMicActive(false); // Disable mic when sleeping
        setIsWakingUp(false); // Reset wake-up flag
        console.log('✅ Frontend set to Sleeping state');
      }
      // Handle wake word detection from backend - show "Waking up" temporarily
      else if (sleepStatus === 'Waking up') {
        setJerryState('idle');
        setStatus('Waking up');
        setIsWakingUp(true); // Set wake-up flag to prevent processing status
        console.log('✅ Frontend set to Waking up state');
      }
      // Handle awake state from backend
      else if (sleepStatus === 'Awake') {
        if (status === 'Sleeping' || status === 'Waking up') {
          // When transitioning from sleep via wake word, don't change status yet
          // Keep showing "Waking up" with sleeping emoji until bot actually speaks
          // Only update internal state flags
          setIsMicActive(true);
          setHasWokenUp(true);
          // Keep the current status and emoji - don't change to Speaking yet
          console.log('✅ Frontend received Awake state during wake-up (keeping Waking up status until bot speaks)');
        } else {
          // Already awake, just ensure mic is active
          setIsMicActive(true);
          console.log('✅ Frontend already awake, mic activated');
        }
      }
    }
  }, [sleepStatus, status]);

  // Connect Pipecat events to character state
  useEffect(() => {
    if (!client) return;

    const handleUserStartedSpeaking = () => {
      console.log('🎤 UserStartedSpeaking event fired, sleepStatus:', sleepStatus);
      // Completely ignore VAD events when sleeping - backend is authoritative
      if (sleepStatus === 'Sleeping') {
        console.log('User speaking while sleeping - ignoring VAD event, backend is authoritative');
        return;
      }
      // Only process VAD events when backend says we're awake
      if (sleepStatus === 'Awake' || sleepStatus === 'Waking up') {
        setJerryState('listening'); // User speaks → listening
        setStatus('Listening');
        setLastUserActivity(Date.now()); // Update last activity timestamp
      }
    };
    const handleUserStoppedSpeaking = () => {
      console.log('🛑 UserStoppedSpeaking event fired, sleepStatus:', sleepStatus);
      
      // Don't change status during wake-up transition - let wake-up flow control it
      if (isWakingUp) {
        console.log('User stopped speaking during wake-up transition - ignoring VAD event');
        return;
      }
      
      // Completely ignore VAD events when sleeping - backend is authoritative
      if (sleepStatus === 'Sleeping') {
        console.log('User stopped speaking while sleeping - ignoring VAD event, backend is authoritative');
        return;
      }
      
      // Show "Ready" only once during first initialization
      if (!hasWokenUp && !hasShownReady) {
        console.log('UserStoppedSpeaking - showing Ready (first init)');
        setJerryState('success'); // Keep smile face during first init
        setStatus('Ready');
        setHasShownReady(true);
      } else if (!hasWokenUp) {
        console.log('UserStoppedSpeaking - showing success (first init)');
        setJerryState('success'); // Keep smile face during first init
        // Don't set status again - already shown "Ready"
      } else if (sleepStatus === 'Awake') {
        console.log('UserStoppedSpeaking - showing Thinking');
        setJerryState('thinking'); // User stops → thinking
        setStatus('Thinking');
      }
    };
    const handleBotLlmStarted = () => {
      console.log('🧠 BotLlmStarted event fired');
      // Don't show processing during wake-up transition - let wake-up flow control it
      if (isWakingUp) {
        console.log('BotLlmStarted during wake-up transition - ignoring, keeping wake-up flow');
        return;
      }
      // Show processing during normal operation
      console.log('BotLlmStarted - showing Processing');
      setJerryState('processing'); // LLM thinking → processing
      setStatus('Processing');
    };
    const handleFunctionCallStarted = () => {
      console.log('⚙️ FunctionCallStarted event fired');
      // Don't show processing during wake-up transition - let wake-up flow control it
      if (isWakingUp) {
        console.log('FunctionCallStarted during wake-up transition - ignoring, keeping wake-up flow');
        return;
      }
      // Only show processing during normal operation (not first init)
      if (hasWokenUp) {
        console.log('FunctionCallStarted - showing Processing');
        setJerryState('processing'); // Function call → processing
        setStatus('Processing');
      } else {
        console.log('FunctionCallStarted - ignoring (first init)');
      }
    };
    const handleBotTtsStarted = () => {
      console.log('🔊 BotTtsStarted event fired');
      // Don't change state on TTS start - let BotStartedSpeaking handle the transition to speaking
      // This prevents the processing state from overriding the speaking state
      console.log('BotTtsStarted - waiting for BotStartedSpeaking');
    };
    const handleBotStartedSpeaking = () => {
      setJerryState('speaking'); // Bot speaks → speaking (when audio actually plays)
      setStatus('Speaking');
      // Activate mic button visually when bot starts speaking
      setIsMicActive(true);
      // Clear wake-up flag when bot actually starts speaking
      setIsWakingUp(false);
      console.log('🎯 Bot started speaking - transitioning to Speaking state');
    };
    const handleBotStoppedSpeaking = () => {
      setJerryState('listening'); // Bot stops → listening (waiting for user)
      setStatus('Listening');
      // Keep mic active - user can still talk
      
      // Track when bot stopped speaking for timeout calculation
      setLastBotSpeechEnd(Date.now());
      console.log('🎯 Bot stopped speaking, starting 30s timeout timer');
    };
    const handleBotReady = () => {
      console.log('🎯 BotReady event fired');
      // On first init, we already show Ready state, so just activate mic
      if (!hasWokenUp) {
        console.log('BotReady - first init, activating mic');
        setHasWokenUp(true);
        setIsMicActive(true); // Activate mic on ready
        // Keep Ready status and success state (already set in initial state)
      } else {
        console.log('BotReady - showing Listening (normal operation)');
        setJerryState('listening'); // After first wake up, go to listening
        setStatus('Listening');
      }
    };
    
    const handleBotDisconnected = () => {
      setHasWokenUp(false); // Reset wake up flag
      setJerryState('idle'); // Bot disconnected → sleeping
      setStatus('Sleeping');
      setIsMicActive(false); // Deactivate mic button
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
  }, [client, hasWokenUp, hasShownReady, isWakingUp]);

  // Auto-sleep timer: if user doesn't speak for 30 seconds after bot stops speaking, agent goes to sleep
  useEffect(() => {
    const checkInactivity = () => {
      // Auto-sleep is now handled by backend - frontend just syncs with backend sleep state
      // This prevents conflicts between frontend and backend sleep logic
      // The backend handles the 30-second timeout and sends sleep state updates to frontend
    };

    // Check every 1 second for better responsiveness
    const intervalId = setInterval(checkInactivity, 1000);

    return () => {
      clearInterval(intervalId);
    };
  }, [lastUserActivity, lastBotSpeechEnd, isMicActive, client, status, isConnected, hasShownReady]);

  const toggleRecording = async () => {
    if (isMicActive) {
      await stopRecording();
    } else {
      await startRecording();
    }
  };

  const startRecording = async () => {
    try {
      setIsLoading(true);
      
      // Manual wake removed - only wake word detection is supported
      // If agent is sleeping, user must say wake word
      if (status === 'Sleeping') {
        console.log('Agent sleeping - say "wake up" to wake the agent');
        setIsLoading(false);
        return;
      }
      
      setStatus('Waking up');
      setJerryState('success'); // Show smile face during initialization
      
      if (!client) {
        setStatus('Error');
        setJerryState('error');
        return;
      }

      // Connect if not already connected
      if (!isConnected) {
        const connectStartTime = performance.now();
        console.log('Starting Pipecat connection...');
        await client.connect();
        const connectEndTime = performance.now();
        const connectionTime = (connectEndTime - connectStartTime).toFixed(2);
        console.log(`Pipecat connection completed in ${connectionTime}ms`);
        setIsConnected(true);
        // Auto-wake on first connection - backend will handle this
        setStatus('Listening');
        setJerryState('listening');
        setIsMicActive(true);
        setIsLoading(false);
        return;
      }

      // Activate mic button
      setIsMicActive(true);
      
      // Go directly to listening
      setStatus('Listening');
      setJerryState('listening');
      setIsMicActive(true);
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

      console.log('🛑 Stopping recording');
      setJerryState('idle');
      setStatus('Sleeping');
      setIsMicActive(false);
      
      // Manual sleep removed - backend will auto-sleep after 30s timeout
      // Just disconnect the client to stop audio processing when mic is off
      try {
        if (isConnected) {
          console.log('🔌 Disconnecting Pipecat client to stop audio processing');
          await client.disconnect();
          setIsConnected(false);
          console.log('✅ Pipecat client disconnected');
        }
      } catch (err) {
        console.error('❌ Error disconnecting client:', err);
      }
    } catch (err) {
      console.error(err);
    }
  };

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
      <div className="lottie-character" style={{width: '100%', height: '280px'}}>
        <VoiceEmoji state={jerryState} />
      </div>

      {/* Status Text */}
      <p style={{
        fontSize: '1.25rem',
        color: '#64748B',
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
          opacity: isMicActive ? 0.6 : 0,
          animation: isMicActive ? `pulse 2s ease-out infinite` : 'none',
        }}></div>
        <div style={{
          position: 'absolute',
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          border: '2px solid rgba(14, 165, 233, 0.4)',
          opacity: isMicActive ? 0.5 : 0,
          animation: isMicActive ? `pulse 2s ease-out infinite 0.3s` : 'none',
        }}></div>
        <div style={{
          position: 'absolute',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          border: '2px solid rgba(14, 165, 233, 0.5)',
          opacity: isMicActive ? 0.4 : 0,
          animation: isMicActive ? `pulse 2s ease-out infinite 0.6s` : 'none',
        }}></div>

        {/* Main Button */}
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: isMicActive ? '#0ea5e9' : 'white',
          border: '3px solid white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 4px 20px #0ea5e940`,
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          opacity: isLoading ? 0.5 : 1,
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={isMicActive ? 'white' : '#0ea5e9'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="22"/>
          </svg>
        </div>
      </div>
    </div>
  );
};
