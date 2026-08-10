import { useState, useEffect, useRef } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { WebSocketTransport, ProtobufFrameSerializer } from '@pipecat-ai/websocket-transport';
import { VoiceSessionCard } from './VoiceSessionCard';

export const VoiceAssistant = () => {
  const [userSub, setUserSub] = useState('');
  const [client, setClient] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const clientRef = useRef<any>(null);

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
      {/* Blue patches / soft blobs */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: '-120px',
          left: '-100px',
          width: '420px',
          height: '420px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, #BFD7FF 0%, rgba(191,215,255,0) 70%)',
          filter: 'blur(10px)',
          pointerEvents: 'none',
        }}
      />
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          bottom: '-140px',
          right: '-120px',
          width: '480px',
          height: '480px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, #DCE9FF 0%, rgba(220,233,255,0) 70%)',
          filter: 'blur(10px)',
          pointerEvents: 'none',
        }}
      />
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: '35%',
          right: '8%',
          width: '220px',
          height: '220px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, #A9C9FF 0%, rgba(169,201,255,0) 75%)',
          filter: 'blur(8px)',
          pointerEvents: 'none',
        }}
      />

      {/* Navigation Header */}
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 32px',
          background: 'white',
          borderBottom: '1px solid #E8F0FF',
          zIndex: 100,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
          <button
            onClick={() => window.location.href = '/profile'}
            style={{
              padding: '10px 20px',
              background: 'white',
              border: '1px solid #E8F0FF',
              borderRadius: '8px',
              color: '#14213D',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = '#F7F9FC'}
            onMouseOut={(e) => e.currentTarget.style.background = 'white'}
          >
            Profile
          </button>
          <button
            onClick={() => window.location.href = '/documents'}
            style={{
              padding: '10px 20px',
              background: 'white',
              border: '1px solid #E8F0FF',
              borderRadius: '8px',
              color: '#14213D',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = '#F7F9FC'}
            onMouseOut={(e) => e.currentTarget.style.background = 'white'}
          >
            Documents
          </button>
        </div>
        <button
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
          style={{
            padding: '10px 20px',
            background: 'white',
            border: '1px solid #E8F0FF',
            borderRadius: '8px',
            color: '#DC2626',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => e.currentTarget.style.background = '#FEF2F2'}
          onMouseOut={(e) => e.currentTarget.style.background = 'white'}
        >
          Logout
        </button>
      </nav>

      {/* Main Content */}
      <div
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
          <div style={{textAlign: 'center'}}>
            <div style={{
              width: '48px',
              height: '48px',
              border: '4px solid #E8F0FF',
              borderTop: '4px solid #0ea5e9',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 16px'
            }}></div>
            <p style={{color: '#64748B', marginTop: '16px'}}>Connecting to your assistant...</p>
          </div>
        )}
        
        {error && (
          <div style={{
            background: 'white',
            padding: '24px 32px',
            borderRadius: '16px',
            border: '1px solid #FFD6D6',
            maxWidth: '400px',
            textAlign: 'center'
          }}>
            <div style={{fontSize: '2rem', marginBottom: '8px'}}>⚠️</div>
            <h3 style={{color: '#DC2626', marginBottom: '8px'}}>Connection failed</h3>
            <p style={{color: '#64748B'}}>{error}</p>
          </div>
        )}
        
        {!loading && !error && client && <VoiceSessionCard userSub={userSub} client={client} />}
      </div>
    </main>
  );
};
