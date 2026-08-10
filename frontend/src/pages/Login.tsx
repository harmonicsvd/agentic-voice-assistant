export const Login = () => {
  const handleLogin = () => {
    // Call actual Google OAuth endpoint - proxied through Vite
    window.location.href = '/auth/google/login';
  };

  return (
    <main
      className="page"
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '24px',
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

      <div
        style={{
          position: 'relative',
          zIndex: 1,
          width: '100%',
          maxWidth: '480px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
        }}
      >
        <h1
          className="hero-title"
          style={{
            display: 'block',
            width: 'fit-content',
            maxWidth: 'none',
            margin: '0 auto 32px auto',
            textAlign: 'center',
            fontSize: 'clamp(1.4rem, 4vw, 3rem)',
            fontWeight: 700,
            lineHeight: 1.15,
            color: '#14213D',
            whiteSpace: 'nowrap',
            transform: 'translateX(-60px)',
          }}
        >
          Your personal voice assistant.
        </h1>

        <button
          className="signin-btn"
          onClick={handleLogin}
          style={{
            width: '100%',
            padding: '16px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}
        >
          <span className="signin-icon google-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16">
              <path
                fill="#EA4335"
                d="M12 10.2v3.9h5.4c-.2 1.3-1.5 3.9-5.4 3.9-3.2 0-5.9-2.7-5.9-6s2.7-6 5.9-6c1.8 0 3 .8 3.7 1.5l2.5-2.4C16.6 3.6 14.5 2.7 12 2.7 6.9 2.7 2.8 6.8 2.8 12s4.1 9.3 9.2 9.3c5.3 0 8.8-3.7 8.8-8.9 0-.6-.1-1.1-.2-1.5H12z"
              />
              <path
                fill="#34A853"
                d="M2.8 12c0 1.8.7 3.5 1.8 4.8l3-2.4c-.4-.7-.7-1.5-.7-2.4s.2-1.7.7-2.4l-3-2.4C3.5 8.5 2.8 10.2 2.8 12z"
              />
              <path
                fill="#FBBC05"
                d="M12 21.3c2.5 0 4.6-.8 6.2-2.3l-3-2.4c-.8.6-1.8 1-3.2 1-2.5 0-4.6-1.7-5.3-4l-3.1 2.4c1.6 3.1 4.8 5.3 8.4 5.3z"
              />
              <path
                fill="#4285F4"
                d="M6.7 13.6c-.2-.5-.3-1-.3-1.6s.1-1.1.3-1.6l-3.1-2.4C2.9 9.2 2.8 10.6 2.8 12s.1 2.8.8 4l3.1-2.4z"
              />
            </svg>
          </span>
          <span>Continue with Google</span>
        </button>
      </div>
    </main>
  );
};