export const Login = () => {

  const handleLogin = () => {
    // Call actual Google OAuth endpoint - proxied through Vite
    window.location.href = '/auth/google/login';
  };

  return (
    <main className="page">
      <div className="brandbar">
        <div className="brand-copy">
          <div className="brand-name">Ram - Sham</div>
          <div className="brand-tag">Personal Work Assistant</div>
        </div>
      </div>

      <section className="shell">
        <div className="story">
          <div className="eyebrow">Your personal assistant for work</div>
          <h1 className="hero-title">
            A personal assistant that understands how you work.
          </h1>
          <p className="hero-copy">
            Ram helps you schedule and prepare for meetings while Sham adds
            weather and work-context intelligence behind the scenes.
          </p>
          <div className="chips">
            <div className="chip">Knows your role</div>
            <div className="chip">Remembers your preferences</div>
            <div className="chip">Supports your daily work</div>
          </div>
          <div className="story-stat">
            <span className="story-stat-label">What it helps with</span>
            <strong>Meetings, preparation, and context</strong>
            <p>Built to support your workflow, not just answer one-off questions.</p>
          </div>
        </div>

        <div className="panel">
          <div className="card">
            <div className="card-kicker">Get started</div>
            <h2 className="card-title">Start with Ram - Sham</h2>
            <p className="card-copy">
              Sign in once, set up your role and preferences, and let your
              assistant adapt around how you work.
            </p>

            <div className="card-highlight">
              <strong>Built for a personalized setup</strong>
              <p>
                Your profile helps Ram understand your meetings and gives Sham
                the context needed for practical recommendations.
              </p>
            </div>

            <button className="signin-btn" onClick={handleLogin}>
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

            <p className="trust">
              Your profile helps Ram and Sham personalize meeting and weather guidance.
            </p>

            <div className="steps">
              <p className="steps-title">What you will set up</p>

              <div className="step">
                <div className="step-num">1</div>
                <div>Your role, work style, and preferences</div>
              </div>

              <div className="step">
                <div className="step-num">2</div>
                <div>Your city, timezone, and daily context</div>
              </div>

              <div className="step">
                <div className="step-num">3</div>
                <div>Your assistant experience inside Ram - Sham</div>
              </div>
            </div>

            <p className="card-footnote">
              Calm setup now. Smarter guidance once your profile is in place.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
};
