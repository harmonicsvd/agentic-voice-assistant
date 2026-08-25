import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, Easing } from 'framer-motion';
import { AnimatedBackground } from '../components/motion/AnimatedBackground';
import { EmojiCarousel } from '../components/motion/EmojiCarousel';

interface FormData {
  work_description: string;
  industry: string;
  responsibilities: string;
  company_name: string;
  work_environment: string;
}

export const Setup = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [accentColor, setAccentColor] = useState('#6EB5FF');
  const [formData, setFormData] = useState<FormData>({
    work_description: '',
    industry: '',
    responsibilities: '',
    company_name: '',
    work_environment: '',
  });

  useEffect(() => {
    checkAuth();
    loadProfile();
  }, []);

  const checkAuth = async () => {
    try {
      const voiceAgentUrl = import.meta.env.VITE_VOICE_AGENT_URL || '';
      const res = await fetch(`${voiceAgentUrl}/auth/me`, { credentials: 'include' });
      if (res.status !== 200) {
        navigate('/login');
      }
    } catch (e) {
      console.error('Auth check failed', e);
      navigate('/login');
    }
  };

  const loadProfile = async () => {
    try {
      const voiceAgentUrl = import.meta.env.VITE_VOICE_AGENT_URL || '';
      const response = await fetch(`${voiceAgentUrl}/api/profile`, { credentials: 'same-origin' });
      if (!response.ok) return;
      const payload = await response.json();
      const profile = payload.profile || {};

      if (payload.is_setup_complete) {
        window.location.href = '/assistant';
        return;
      }

      if (profile.work_description) setFormData(prev => ({ ...prev, work_description: profile.work_description }));
      if (profile.industry) setFormData(prev => ({ ...prev, industry: profile.industry }));
      if (profile.responsibilities) setFormData(prev => ({ ...prev, responsibilities: profile.responsibilities }));
      if (profile.company_name) setFormData(prev => ({ ...prev, company_name: profile.company_name }));
      if (profile.work_environment) setFormData(prev => ({ ...prev, work_environment: profile.work_environment }));
    } catch (_err) {
      // Silent error handling
    }
  };

  const validateCurrentStep = (): boolean => {
    setError('');

    if (currentStep === 1) {
      if (!formData.work_description.trim()) {
        setError('Please describe your work before continuing.');
        return false;
      }
      if (!formData.industry.trim()) {
        setError('Please specify your industry.');
        return false;
      }
    }

    if (currentStep === 2) {
      if (!formData.responsibilities.trim()) {
        setError('Please describe your main responsibilities.');
        return false;
      }
      if (!formData.company_name.trim()) {
        setError('Please add your company name.');
        return false;
      }
      if (!formData.work_environment.trim()) {
        setError('Please specify your work environment.');
        return false;
      }
    }

    return true;
  };

  const handleNext = async () => {
    if (!validateCurrentStep()) return;

    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
      return;
    }

    await saveProfile();
  };

  const saveProfile = async () => {
    if (saving) return;
    setSaving(true);
    setError('');

    try {
      const voiceAgentUrl = import.meta.env.VITE_VOICE_AGENT_URL || '';
      const response = await fetch(`${voiceAgentUrl}/api/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({}));
        throw new Error(errorPayload.error || 'Could not save your setup.');
      }

      window.location.href = '/assistant';
    } catch (err: any) {
      setError(err.message || 'Could not save your setup.');
      setSaving(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.8,
        ease: "easeOut" as Easing
      }
    }
  };

  const formVariants = {
    hidden: { opacity: 0, x: 50 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut" as Easing,
        delay: 0.3
      }
    }
  };

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

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '24px',
          gap: '48px',
        }}
      >
        {/* Left side - Emoji Carousel with proper container */}
        <div
          style={{
            width: '100%',
            maxWidth: '600px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            marginRight: '32px',
            flexShrink: 0,
          }}
        >
          <EmojiCarousel onColorChange={setAccentColor} />
          <p
            style={{
              fontSize: '1.25rem',
              color: 'var(--text-soft)',
              textAlign: 'center',
              marginTop: '24px',
            }}
          >
            Let's get to know you
          </p>
        </div>

        {/* Right side - Form */}
        <motion.div
          variants={formVariants}
          style={{
            width: '100%',
            maxWidth: '480px',
            background: 'white',
            borderRadius: '24px',
            padding: '32px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
          }}
        >
          {/* Progress indicator */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-soft)' }}>
                Step {currentStep} of 2
              </span>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-soft)' }}>
                {Math.round((currentStep / 2) * 100)}%
              </span>
            </div>
            <div style={{ height: '4px', background: '#E8F0FF', borderRadius: '2px' }}>
              <div
                style={{
                  height: '100%',
                  width: `${(currentStep / 2) * 100}%`,
                  background: accentColor,
                  borderRadius: '2px',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>

          {/* Form content */}
          {currentStep === 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" as Easing }}
            >
              <h2 style={{ fontSize: '1.5rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                Tell us about your work
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-soft)', marginBottom: '24px' }}>
                Help us understand what you do
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                    What describes your work best?
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Software Development, Construction, Healthcare"
                    value={formData.work_description}
                    onChange={(e) => setFormData({ ...formData, work_description: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #E8F0FF',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = accentColor}
                    onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                    What industry do you work in?
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Technology, Healthcare, Finance"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #E8F0FF',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = accentColor}
                    onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {currentStep === 2 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" as Easing }}
            >
              <h2 style={{ fontSize: '1.5rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                Your role details
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-soft)', marginBottom: '24px' }}>
                More context about your position
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                    What are your main responsibilities?
                  </label>
                  <textarea
                    placeholder="Briefly describe your daily tasks and responsibilities"
                    value={formData.responsibilities}
                    onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
                    rows={3}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #E8F0FF',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                      resize: 'vertical',
                    }}
                    onFocus={(e) => e.target.style.borderColor = accentColor}
                    onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                    Company name
                  </label>
                  <input
                    type="text"
                    placeholder="Your company name"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #E8F0FF',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = accentColor}
                    onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: 'var(--text-main)' }}>
                    Work environment
                  </label>
                  <select
                    value={formData.work_environment}
                    onChange={(e) => setFormData({ ...formData, work_environment: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #E8F0FF',
                      borderRadius: '12px',
                      fontSize: '1rem',
                      outline: 'none',
                      transition: 'border-color 0.2s',
                      backgroundColor: 'white',
                    }}
                    onFocus={(e) => e.target.style.borderColor = accentColor}
                    onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                  >
                    <option value="">Select work environment</option>
                    <option>Hybrid</option>
                    <option>Remote</option>
                    <option>Office</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                padding: '12px 16px',
                background: '#FEE2E2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                color: '#DC2626',
                fontSize: '0.875rem',
                marginTop: '16px',
              }}
            >
              {error}
            </motion.div>
          )}

          {/* Navigation buttons */}
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
            <motion.button
              type="button"
              onClick={() => setCurrentStep(currentStep - 1)}
              disabled={currentStep === 1 || saving}
              whileHover={{ scale: currentStep === 1 || saving ? 1 : 1.02 }}
              whileTap={{ scale: currentStep === 1 || saving ? 1 : 0.98 }}
              style={{
                flex: 1,
                padding: '14px',
                border: '1px solid #E8F0FF',
                borderRadius: '12px',
                background: 'white',
                color: 'var(--text-main)',
                fontSize: '1rem',
                cursor: currentStep === 1 || saving ? 'not-allowed' : 'pointer',
                opacity: currentStep === 1 ? 0.5 : 1,
                transition: 'all 0.2s',
              }}
            >
              Back
            </motion.button>
            <motion.button
              type="button"
              onClick={handleNext}
              disabled={saving}
              whileHover={{ scale: saving ? 1 : 1.02 }}
              whileTap={{ scale: saving ? 1 : 0.98 }}
              style={{
                flex: 1,
                padding: '14px',
                border: 'none',
                borderRadius: '12px',
                background: accentColor,
                color: 'white',
                fontSize: '1rem',
                cursor: saving ? 'not-allowed' : 'pointer',
                opacity: saving ? 0.7 : 1,
                transition: 'all 0.2s',
              }}
            >
              {saving ? 'Saving...' : currentStep === 2 ? 'Complete setup' : 'Continue'}
            </motion.button>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--text-soft)', textAlign: 'center', marginTop: '16px' }}>
            You can update these details later in your profile
          </p>
        </motion.div>
      </motion.div>
    </main>
  );
};