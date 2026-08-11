import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, MapPin, Clock, Briefcase, Shield, CheckCircle, AlertCircle, Loader2, Save, ArrowLeft } from 'lucide-react';

export const Profile = () => {
  const navigate = useNavigate();
  const [userSub, setUserSub] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [profile, setProfile] = useState({
    email: '',
    name: '',
    work_description: '',
    industry: '',
    responsibilities: '',
    company_name: '',
    work_environment: '',
  });
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    checkAuth();
    loadProfile();
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch('/auth/me', { credentials: 'include' });
      if (res.status === 200) {
        const me = await res.json();
        const sub = me.user?.sub || '';
        setUserSub(sub);
      } else {
        navigate('/login');
      }
    } catch (e) {
      console.error('Auth check failed', e);
      navigate('/login');
    }
  };

  const loadProfile = async () => {
    try {
      const response = await fetch('/profile', { credentials: 'same-origin' });
      if (!response.ok) {
        navigate('/login');
        return;
      }
      const payload = await response.json();
      if (payload.profile) {
        setProfile(payload.profile);
      }
    } catch (err) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/profile', {
        method: 'PUT',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profile),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save profile');
      }

      setSuccess('Profile updated successfully!');
      setEditMode(false);
    } catch (err: any) {
      setError(err.message || 'Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[var(--teal)] animate-spin" />
      </div>
    );
  }

  return (
    <main className="page">
      <div className="brandbar">
        <div className="brand-copy">
          <div className="brand-name">Ram - Sham</div>
          <div className="brand-tag">Personal Work Assistant</div>
        </div>
        <div className="brand-actions">
          <button className="nav-btn" type="button" onClick={() => navigate('/assistant')}>
            Assistant
          </button>
          <button className="nav-btn" type="button" onClick={() => navigate('/documents')}>
            Documents
          </button>
          <button className="logout-btn" type="button" onClick={async () => {
            try {
              await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
              });
            } finally {
              window.location.href = '/login';
            }
          }}>
            Logout
          </button>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-8 py-10">
        <button
          onClick={() => navigate('/assistant')}
          className="mb-8 px-4 py-2.5 bg-white/60 hover:bg-white/80 text-[var(--text-main)] rounded-lg transition-all duration-300 flex items-center gap-2 font-medium border border-[var(--line)]"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Assistant
        </button>
        
        <div className="mb-10">
          <h1 className="text-4xl font-bold text-[var(--text-main)] mb-3">
            Profile Settings
          </h1>
          <p className="text-[var(--text-soft)] text-lg">
            Manage your account preferences and personal information
          </p>
        </div>

        {error && (
          <div className="mb-8 p-5 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-4 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-8 p-5 bg-green-50 border border-green-200 rounded-2xl flex items-center gap-4 text-green-700">
            <CheckCircle className="w-6 h-6" />
            <span className="font-medium">{success}</span>
          </div>
        )}

        {/* Three Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
          {/* Personal Information - 4 columns */}
          <div className="lg:col-span-4 bg-white rounded-2xl p-8 shadow-lg border-l-4 border-[var(--teal)]">
            <h2 className="text-2xl font-semibold text-[var(--text-main)] mb-2 flex items-center gap-3">
              <div className="p-2 bg-[var(--teal-soft)] rounded-lg">
                <User className="w-6 h-6 text-[var(--teal)]" />
              </div>
              Personal Information
            </h2>
            <p className="text-[var(--text-soft)] mb-6">Your basic account details</p>

            <div className="space-y-6">
              <div>
                <label className="block text-[var(--text-soft)] text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  value={profile.email}
                  disabled
                  className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-soft)] disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-[var(--text-soft)] text-sm font-medium mb-2">Name</label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  disabled={!editMode}
                  className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-main)] disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Location & Time - 5 columns */}
          <div className="lg:col-span-5 bg-white rounded-2xl p-8 shadow-lg">
            <h2 className="text-2xl font-semibold text-[var(--text-main)] mb-2 flex items-center gap-3">
              <div className="p-2 bg-[var(--teal-soft)] rounded-lg">
                <MapPin className="w-6 h-6 text-[var(--teal)]" />
              </div>
              Location & Time
            </h2>
            <p className="text-[var(--text-soft)] mb-6">Your location and travel preferences</p>

            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-soft)] mb-4 uppercase tracking-wider">Location</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-[var(--text-soft)] text-sm font-medium mb-2 flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-[var(--teal)]" />
                      Default City
                    </label>
                    <input
                      type="text"
                      value={profile.default_city}
                      onChange={(e) => setProfile({ ...profile, default_city: e.target.value })}
                      disabled={!editMode}
                      className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-main)] disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-[var(--text-soft)] text-sm font-medium mb-2 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-[var(--teal)]" />
                      Timezone
                    </label>
                    <input
                      type="text"
                      value={profile.timezone}
                      onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                      disabled={!editMode}
                      className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-main)] disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-colors"
                    />
                  </div>
                </div>
              </div>

              <div className="border-t border-[var(--line)] pt-6">
                <h3 className="text-sm font-semibold text-[var(--text-soft)] mb-4 uppercase tracking-wider">Commute</h3>
                <div>
                  <label className="block text-[var(--text-soft)] text-sm font-medium mb-2">Commute Mode</label>
                  <input
                    type="text"
                    value={profile.commute_mode}
                    onChange={(e) => setProfile({ ...profile, commute_mode: e.target.value })}
                    disabled={!editMode}
                    className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-main)] disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Work Preferences - 3 columns */}
          <div className="lg:col-span-3 bg-white rounded-2xl p-8 shadow-lg">
            <h2 className="text-2xl font-semibold text-[var(--text-main)] mb-2 flex items-center gap-3">
              <div className="p-2 bg-[var(--teal-soft)] rounded-lg">
                <Shield className="w-6 h-6 text-[var(--teal)]" />
              </div>
              Work Preferences
            </h2>
            <p className="text-[var(--text-soft)] mb-6">Your work style settings</p>

            <div className="space-y-6">
              <div>
                <label className="block text-[var(--text-soft)] text-sm font-medium mb-2">Risk Tolerance</label>
                <input
                  type="text"
                  value={profile.risk_tolerance}
                  onChange={(e) => setProfile({ ...profile, risk_tolerance: e.target.value })}
                  disabled={!editMode}
                  className="w-full px-4 py-3 bg-[var(--bg-sand)] border border-[var(--line)] rounded-xl text-[var(--text-main)] disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-[var(--teal)] transition-colors"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="block text-[var(--text-soft)] text-sm font-medium mb-1">PPE Required</label>
                  <p className="text-[var(--text-soft)] text-xs">For field work</p>
                </div>
                <button
                  onClick={() => setProfile({ ...profile, ppe_required: !profile.ppe_required })}
                  disabled={!editMode}
                  className={`w-12 h-6 rounded-full p-1 transition-colors ${profile.ppe_required ? 'bg-[var(--teal)]' : 'bg-[var(--bg-sand)]'}`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white transition-transform ${profile.ppe_required ? 'translate-x-6' : ''}`} />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          {!editMode ? (
            <button
              onClick={() => setEditMode(true)}
              className="px-6 py-3 bg-[var(--teal)] hover:bg-[var(--teal-deep)] text-white rounded-xl transition-all duration-300 font-medium"
            >
              Edit Profile
            </button>
          ) : (
            <>
              <button
                onClick={() => {
                  setEditMode(false);
                  loadProfile();
                }}
                className="px-6 py-3 bg-white hover:bg-[var(--bg-sand)] text-[var(--text-main)] rounded-xl transition-all duration-300 border border-[var(--line)] font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-3 bg-[var(--teal)] hover:bg-[var(--teal-deep)] disabled:bg-[var(--text-soft)] text-white rounded-xl transition-all duration-300 font-medium flex items-center gap-2"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5" />
                    Save Changes
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </main>
  );
};