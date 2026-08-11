import { useState, useEffect, useRef } from 'react';
import { motion, Easing } from 'framer-motion';
import { PipecatClient } from '@pipecat-ai/client-js';
import { WebSocketTransport, ProtobufFrameSerializer } from '@pipecat-ai/websocket-transport';
import { VoiceSessionCard } from './VoiceSessionCard';
import { AnimatedBackground } from './motion/AnimatedBackground';

export const VoiceAssistant = () => {
  const [userSub, setUserSub] = useState('');
  const [client, setClient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accentColor, setAccentColor] = useState('#F59E0B'); // Default orange for sleeping state
  const clientRef = useRef<any>(null);

  const handleColorChange = (color: string) => {
    setAccentColor(color);
  };

  useEffect(() => {
    // Get user sub from auth - only run once on mount
    const fetchUser = async () => {
      try {
        const res = await fetch('/auth/me', { credentials: 'include' });
        if (res.status === 200) {
          const me = await res.json();
          const sub = me.user?.sub || '';
          setUserSub(sub);

          // Create client AFTER userSub is available, but DON'T auto-connect
          const newClient = new PipecatClient({
            transport: new WebSocketTransport({
              wsUrl: `ws://localhost:8000/ws/pipecat?user_sub=${sub}`,
              serializer: new ProtobufFrameSerializer(),
              recorderSampleRate: 16000,
              playerSampleRate: 24000,
            }),
            enableMic: true,
            enableCam: false,
          }) as any;

          clientRef.current = newClient;
          setClient(newClient);
          setLoading(false);
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


  return (
    <main
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        background: '#F7F9FC',
        overflow: 'hidden',
      }}
    >
      {/* Animated background with floating blobs and particles */}
      <AnimatedBackground accentColor={accentColor} />

      {/* Film grain overlay */}
      <div className="film-grain" aria-hidden="true" />

      {/* Enhanced Navigation Header with motion */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeOut" as Easing }}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 32px',
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(232, 240, 255, 0.6)',
          zIndex: 100,
        }}
      >
        <motion.div 
          style={{display: 'flex', alignItems: 'center', gap: '12px'}}
          initial={{ x: -20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.2 }}
        >
          <motion.button
            onClick={() => window.location.href = '/profile'}
            whileHover={{ scale: 1.05, backgroundColor: 'rgba(247, 249, 252, 0.9)' }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: '10px 20px',
              background: 'white',
              border: '1px solid rgba(232, 240, 255, 0.8)',
              borderRadius: '12px',
              color: '#14213D',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: '0 2px 8px rgba(20, 33, 61, 0.04)',
            }}
          >
            Profile
          </motion.button>
          <motion.button
            onClick={() => window.location.href = '/documents'}
            whileHover={{ scale: 1.05, backgroundColor: 'rgba(247, 249, 252, 0.9)' }}
            whileTap={{ scale: 0.95 }}
            style={{
              padding: '10px 20px',
              background: 'white',
              border: '1px solid rgba(232, 240, 255, 0.8)',
              borderRadius: '12px',
              color: '#14213D',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: '0 2px 8px rgba(20, 33, 61, 0.04)',
            }}
          >
            Documents
          </motion.button>
        </motion.div>
        <motion.button
          onClick={async () => {
            try {
              await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
              });
            } finally {
              window.location.href = '/login';
            }
          }}
          whileHover={{ scale: 1.05, backgroundColor: 'rgba(254, 242, 242, 0.9)' }}
          whileTap={{ scale: 0.95 }}
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.3 }}
          style={{
            padding: '10px 20px',
            background: 'white',
            border: '1px solid rgba(232, 240, 255, 0.8)',
            borderRadius: '12px',
            color: '#DC2626',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 2px 8px rgba(20, 33, 61, 0.04)',
          }}
        >
          Logout
        </motion.button>
      </motion.nav>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" as Easing, delay: 0.4 }}
        style={{
          position: 'relative',
          zIndex: 1,
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 32px 32px',
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
            <p style={{color: '#64748B', marginTop: '16px', fontSize: '1rem', fontWeight: 500}}>Connecting to your assistant...</p>
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
        
        {!loading && !error && client && <VoiceSessionCard userSub={userSub} client={client} onColorChange={handleColorChange} />}
      </motion.div>
    </main>
  );
};
