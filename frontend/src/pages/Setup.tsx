import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const Setup = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    role: '',
    default_city: '',
    timezone: '',
    commute_mode: '',
    risk_tolerance: '',
    ppe_required: false,
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await fetch('/profile', { credentials: 'same-origin' });
      if (!response.ok) return;
      const payload = await response.json();
      const profile = payload.profile || {};

      if (payload.is_setup_complete) {
        window.location.href = '/assistant';
        return;
      }

      if (!formData.timezone && Intl.DateTimeFormat().resolvedOptions().timeZone) {
        setFormData(prev => ({ ...prev, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone }));
      }

      if (profile.role) setFormData(prev => ({ ...prev, role: profile.role }));
      if (profile.default_city) setFormData(prev => ({ ...prev, default_city: profile.default_city }));
      if (profile.timezone) setFormData(prev => ({ ...prev, timezone: profile.timezone }));
      if (profile.commute_mode) setFormData(prev => ({ ...prev, commute_mode: profile.commute_mode }));
      if (profile.risk_tolerance) setFormData(prev => ({ ...prev, risk_tolerance: profile.risk_tolerance }));
      if (typeof profile.ppe_required !== 'undefined') {
        setFormData(prev => ({ ...prev, ppe_required: Boolean(profile.ppe_required) }));
      }
    } catch (_err) {
      if (!formData.timezone && Intl.DateTimeFormat().resolvedOptions().timeZone) {
        setFormData(prev => ({ ...prev, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone }));
      }
    }
  };

  const validateCurrentStep = () => {
    setError('');

    if (currentStep === 1) {
      if (!formData.role.trim()) {
        setError('Please choose your role before continuing.');
        return false;
      }
    }

    if (currentStep === 2) {
      if (!formData.default_city.trim()) {
        setError('Please add your default city.');
        return false;
      }
      if (!formData.timezone.trim()) {
        setError('Please add your timezone.');
        return false;
      }
      if (!formData.commute_mode.trim()) {
        setError('Please choose how you usually commute.');
        return false;
      }
    }

    if (currentStep === 3) {
      if (!formData.risk_tolerance) {
        setError('Please select your risk tolerance.');
        return false;
      }
    }

    return true;
  };

  const handleNext = async () => {
    if (!validateCurrentStep()) return;

    if (currentStep < 3) {
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
      const response = await fetch('/profile', {
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

  return (
    <main className="page">
      <section className="shell shell-setup">
        <div className="story">
          <div className="brandbar brandbar-simple">
            <div className="brand-name">Ram - Sham</div>
            <div className="brand-tag">Personal Work Assistant</div>
          </div>

          <div className="eyebrow">Finish your setup</div>
          <h1 className="hero-title">Set up your personal assistant for work.</h1>
          <p className="hero-copy">
            Ram learns from your role, routines, and preferences. Sham uses your
            work context to add weather-aware preparation guidance behind the scenes.
          </p>

          <div className="benefits">
            <div className="benefit">
              <strong>Role-aware guidance</strong>
              <p>
                Ram uses your setup preferences while Sham adds personalized
                meeting preparation and weather-aware suggestions.
              </p>
            </div>

            <div className="benefit">
              <strong>Built for your daily rhythm</strong>
              <p>
                Your city, timezone, and commute style help Ram and Sham deliver
                practical support when timing and travel matter.
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="progress-row">
            <div className="progress-copy">Step {currentStep} of 3</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${currentStep * 33.333}%` }}></div>
            </div>
          </div>

          <form>
            {currentStep === 1 && (
              <section className="step-panel active">
                <div className="step-tag">Work</div>
                <h2 className="step-title">Tell Ram - Sham about your work</h2>
                <p className="step-copy">
                  Your role helps Ram understand your meetings and helps Sham
                  prepare relevant guidance.
                </p>

                <div className="field-group">
                  <div className="field">
                    <label htmlFor="role">Your role</label>
                    <select
                      id="role"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      required
                    >
                      <option value="">Select your role</option>
                      <option>Architect</option>
                      <option>Contractor</option>
                      <option>Project Manager</option>
                      <option>Site Supervisor</option>
                      <option>Sales Manager</option>
                      <option>Event Coordinator</option>
                      <option>Operations Lead</option>
                      <option>Other</option>
                    </select>
                  </div>
                </div>
              </section>
            )}

            {currentStep === 2 && (
              <section className="step-panel active">
                <div className="step-tag">Context</div>
                <h2 className="step-title">Set your daily context</h2>
                <p className="step-copy">
                  These details help Ram and Sham support travel, timing, and
                  weather-sensitive meetings more practically.
                </p>

                <div className="field-group">
                  <div className="field">
                    <label htmlFor="default_city">Default city</label>
                    <input
                      id="default_city"
                      type="text"
                      placeholder="Berlin"
                      value={formData.default_city}
                      onChange={(e) => setFormData({ ...formData, default_city: e.target.value })}
                      required
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="timezone">Timezone</label>
                    <input
                      id="timezone"
                      type="text"
                      placeholder="Europe/Berlin"
                      value={formData.timezone}
                      onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                      required
                    />
                  </div>

                  <div className="field">
                    <label htmlFor="commute_mode">How do you usually commute?</label>
                    <select
                      id="commute_mode"
                      value={formData.commute_mode}
                      onChange={(e) => setFormData({ ...formData, commute_mode: e.target.value })}
                      required
                    >
                      <option value="">Choose a commute style</option>
                      <option>Car</option>
                      <option>Public transport</option>
                      <option>Walk</option>
                      <option>Bike</option>
                      <option>Mixed</option>
                    </select>
                  </div>
                </div>
              </section>
            )}

            {currentStep === 3 && (
              <section className="step-panel active">
                <div className="step-tag">Preferences</div>
                <h2 className="step-title">Set your preferences</h2>
                <p className="step-copy">
                  Ram and Sham use these preferences to shape how cautious and practical
                  its guidance should be.
                </p>

                <div className="field-group">
                  <div className="field">
                    <label>Risk tolerance</label>
                    <div className="choice-row">
                      <label className="choice-option">
                        <input
                          type="radio"
                          name="risk_tolerance"
                          value="Low"
                          checked={formData.risk_tolerance === 'Low'}
                          onChange={(e) => setFormData({ ...formData, risk_tolerance: e.target.value })}
                          required
                        />
                        <span>Low</span>
                      </label>
                      <label className="choice-option">
                        <input
                          type="radio"
                          name="risk_tolerance"
                          value="Medium"
                          checked={formData.risk_tolerance === 'Medium'}
                          onChange={(e) => setFormData({ ...formData, risk_tolerance: e.target.value })}
                          required
                        />
                        <span>Medium</span>
                      </label>
                      <label className="choice-option">
                        <input
                          type="radio"
                          name="risk_tolerance"
                          value="High"
                          checked={formData.risk_tolerance === 'High'}
                          onChange={(e) => setFormData({ ...formData, risk_tolerance: e.target.value })}
                          required
                        />
                        <span>High</span>
                      </label>
                    </div>
                  </div>

                  <div className="ppe-row">
                    <div className="ppe-copy">
                      <strong>PPE requirements</strong>
                      <p>Turn this on if your work often involves protective equipment.</p>
                    </div>
                    <label className="switch" aria-label="PPE required">
                      <input
                        id="ppe_required"
                        type="checkbox"
                        checked={formData.ppe_required}
                        onChange={(e) => setFormData({ ...formData, ppe_required: e.target.checked })}
                      />
                      <span className="switch-track"></span>
                      <span className="switch-thumb"></span>
                    </label>
                  </div>
                </div>
              </section>
            )}

            {error && <p className="error visible">{error}</p>}

            <div className="actions">
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setCurrentStep(currentStep - 1)}
                disabled={currentStep === 1 || saving}
                style={{ visibility: currentStep === 1 ? 'hidden' : 'visible' }}
              >
                Back
              </button>
              <button
                className="btn btn-primary"
                type="button"
                onClick={handleNext}
                disabled={saving}
              >
                {saving ? 'Saving...' : currentStep === 3 ? 'Finish setup' : 'Continue'}
              </button>
            </div>

            <div className="status-note">
              You can update these details later in your profile.
            </div>
          </form>
        </div>
      </section>
    </main>
  );
};
