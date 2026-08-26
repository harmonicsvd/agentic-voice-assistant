import { useState, useEffect, useRef } from 'react';
import { motion, Easing } from 'framer-motion';
import { PipecatClient, RTVIEvent } from '@pipecat-ai/client-js';
import { WebSocketTransport, ProtobufFrameSerializer } from '@pipecat-ai/websocket-transport';
import { VoiceSessionCard } from './VoiceSessionCard';
import { AnimatedBackground } from './motion/AnimatedBackground';
import { ResponsiveNav } from './ResponsiveNav';
import { SideNav } from './SideNav';
import { TourGuide, hasTourCompleted, resetTour } from './TourGuide';
import { Info } from 'lucide-react';


export const VoiceAssistant = () => {
  const [userSub, setUserSub] = useState('');
  const [client, setClient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sleepStatus, setSleepStatus] = useState<string | undefined>(undefined); // Don't set initial status
  const clientRef = useRef<any>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const [runTour, setRunTour] = useState(false);
  const [tourCompleted, setTourCompleted] = useState(hasTourCompleted());

 useEffect(() => {
  // Get user sub from auth - only run once on mount
  const fetchUser = async () => {
    try {
      const voiceAgentUrl = import.meta.env.VITE_VOICE_AGENT_URL || '';
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const res = await fetch(`${voiceAgentUrl}/auth/me`, { headers });
      if (res.status === 200) {
        const me = await res.json();
        const sub = me.user?.sub || '';
        setUserSub(sub);

        // Create client and connect immediately after userSub is available
        const wsUrl = voiceAgentUrl.replace('http://', 'ws://').replace('https://', 'wss://');
        
        const newClient = new PipecatClient({
          transport: new WebSocketTransport({
            wsUrl: `${wsUrl}/ws/pipecat?user_sub=${sub}`,
            serializer: new ProtobufFrameSerializer(),
            recorderSampleRate: 16000,
            playerSampleRate: 24000,
          }),
          enableMic: true,
          enableCam: false,
        }) as any;

        clientRef.current = newClient;
        setClient(newClient);
        
        // Connect immediately and listen for BotReady event
        try {
          await newClient.connect();
          console.log('Pipecat connected successfully');
        } catch (connectError) {
          console.error('Pipecat connection failed:', connectError);
          setError('Failed to connect to voice assistant');
          setLoading(false);
          return;
        }
        // Listen for BotReady event to know when Pipecat is fully ready
        newClient.on(RTVIEvent.BotReady, () => {
          console.log('Pipecat bot is ready');
          
          // Pre-warm audio context before hiding spinner
          console.log('Pre-warming audio context...');
          try {
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            
            // Resume audio context if suspended
            if (audioContext.state === 'suspended') {
              audioContext.resume().then(() => {
                console.log('AudioContext resumed');
              }).catch(err => {
                console.warn('AudioContext resume failed:', err);
              });
            }
            
            // Create a compressor to prevent sudden volume spikes
            const compressor = audioContext.createDynamicsCompressor();
            compressor.threshold.setValueAtTime(-24, audioContext.currentTime);
            compressor.knee.setValueAtTime(30, audioContext.currentTime);
            compressor.ratio.setValueAtTime(12, audioContext.currentTime);
            compressor.attack.setValueAtTime(0.003, audioContext.currentTime);
            compressor.release.setValueAtTime(0.25, audioContext.currentTime);
            compressor.connect(audioContext.destination);
            
            // Create a gain node for smooth audio fade-in with exponential curve
            const gainNode = audioContext.createGain();
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.7, audioContext.currentTime + 0.8); // 800ms exponential fade-in to 70% volume
            gainNode.connect(compressor);
            
            // Create a silent buffer to warm up the audio pipeline with fade-in
            const silentBuffer = audioContext.createBuffer(1, audioContext.sampleRate, audioContext.sampleRate);
            const source = audioContext.createBufferSource();
            source.buffer = silentBuffer;
            source.connect(gainNode);
            source.start();
            source.stop(audioContext.currentTime + 0.8);
            
            console.log('Audio context pre-warmed with smooth fade-in and compression');
          } catch (audioError) {
            console.warn('Audio context pre-warm failed:', audioError);
            // Continue anyway - audio should still work
          }
          
          // Add a small delay to ensure audio pipeline is fully ready and fade-in completes
          setTimeout(() => {
            console.log('Audio warm-up delay complete, hiding spinner');
            setLoading(false);
          }, 1500); // 1.5s delay to account for 800ms fade-in + buffer
          
          // Listen for RTVI server messages for sleep state updates
          newClient.on(RTVIEvent.ServerMessage, (message: any) => {
            console.log('📥 RTVI server message received:', message);
            console.log('📥 Message structure:', JSON.stringify(message));
            
            // Handle different message structures
            let sleepState = null;
            let isSleeping = null;
            
            // Check direct properties
            if (message.sleep_state) {
              sleepState = message.sleep_state;
            } else if (message.data && message.data.sleep_state) {
              sleepState = message.data.sleep_state;
            }
            
            // Also check for sleeping boolean
            if (message.sleeping !== undefined) {
              isSleeping = message.sleeping;
            } else if (message.data && message.data.sleeping !== undefined) {
              isSleeping = message.data.sleeping;
            }
            
            if (sleepState) {
              console.log('📥 Sleep state update from RTVI:', sleepState);
              setSleepStatus(sleepState);
            } else if (isSleeping !== null) {
              console.log('📥 Sleeping boolean from RTVI:', isSleeping);
              setSleepStatus(isSleeping ? 'Sleeping' : 'Awake');
            } else {
              console.log('📥 RTVI message without sleep state:', message);
            }
          });
        });


        // Fallback: set loading to false after timeout if ready event doesn't fire
        setTimeout(() => {
          console.log('BotReady timeout - hiding spinner anyway');
          setLoading(false);
        }, 10000); // Increased to 10s to account for audio warm-up + fade-in + 3s delay

      } else {
        setError('Authentication failed');
        setLoading(false);
      }
    } catch (e) {
      console.error('Auth check failed', e);
      setError('Failed to connect to backend');
      setLoading(false);
    }
  };

  fetchUser();

  return () => {
    if (clientRef.current) {
      try {
        clientRef.current.disconnect();
      } catch (e) {
        console.error('Failed to disconnect client on cleanup', e);
      }
    }
  };
}, []); // Empty dependency array - only run once on mount

  // Detect desktop vs mobile for content layout adjustment
  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(window.innerWidth >= 768);
    };

    checkDesktop();
    window.addEventListener('resize', checkDesktop);
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  // Check if tour should run on first-time login
  useEffect(() => {
    if (!loading && !error && !tourCompleted) {
      // Delay tour start to ensure UI is fully rendered
      const timer = setTimeout(() => {
        setRunTour(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [loading, error, tourCompleted]);

  const handleReplayTour = () => {
    resetTour();
    setTourCompleted(false);
    setRunTour(true);
  };

  const handleTourComplete = () => {
    setTourCompleted(true);
    setRunTour(false);
  };

  return (
    <>
      <main
        style={{
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          background: '#F7F9FC',
          overflow: 'hidden',
          paddingBottom: '120px', // Space for bottom nav
        }}
      >
      {/* Animated background with floating blobs and particles */}
      <AnimatedBackground />

      {/* Film grain overlay */}
      <div className="film-grain" aria-hidden="true" />

      {/* Side Navigation */}
      <SideNav />

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" as Easing }}
        style={{
          position: 'relative',
          zIndex: 1,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px',
          marginLeft: isDesktop ? '80px' : '0',
        }}
      >
        {loading && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" as Easing }}
            style={{textAlign: 'center'}}
          >
            <div style={{
              width: '48px',
              height: '48px',
              border: '4px solid #E8F0FF',
              borderTop: '4px solid #0ea5e9',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 16px'
            }}></div>
            <p style={{color: '#64748B', marginTop: '16px', fontSize: '1rem', fontWeight: 500}}>Initializing EMO...</p>
          </motion.div>
        )}
        
        {error && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" as Easing }}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(12px)',
              padding: '24px 32px',
              borderRadius: '20px',
              border: '1px solid #FFD6D6',
              maxWidth: '400px',
              textAlign: 'center',
              boxShadow: '0 12px 40px rgba(220, 38, 38, 0.1)'
            }}
          >
            <div style={{fontSize: '2rem', marginBottom: '8px'}}>⚠️</div>
            <h3 style={{color: '#DC2626', marginBottom: '8px', fontFamily: '"Space Grotesk", sans-serif'}}>Connection failed</h3>
            <p style={{color: '#64748B'}}>{error}</p>
          </motion.div>
        )}

        
        
        {!loading && !error && client && <VoiceSessionCard userSub={userSub} client={client} sleepStatus={sleepStatus} />}
      </motion.div>

      {/* Responsive Navigation */}
      <div className="bottom-nav">
        <ResponsiveNav />
      </div>
    </main>

    {/* Tour replay button - small info icon at top right */}
    {tourCompleted && (
      <motion.button
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handleReplayTour}
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 100000,
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(14, 165, 233, 0.3)',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        title="Show tour guide"
      >
        <Info size={20} color="#0ea5e9" />
      </motion.button>
    )}

    {/* Tour Guide - moved outside main for higher z-index */}
    <TourGuide run={runTour} onTourComplete={handleTourComplete} />
    </>
  );
};