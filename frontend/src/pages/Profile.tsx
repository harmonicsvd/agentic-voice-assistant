import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, Easing, AnimatePresence } from 'framer-motion';
import { ResponsiveNav } from '../components/ResponsiveNav';
import { SideNav } from '../components/SideNav';
import { AnimatedBackground } from '../components/motion/AnimatedBackground';
import { useLottie } from 'lottie-react'; // Import Lottie hook

interface ProfileData {
  sub: string;
  email: string;
  name: string | null;
  work_description: string | null;
  industry: string | null;
  responsibilities: string | null;
  company_name: string | null;
  work_environment: string | null;
  emo_avatar: string | null;
  updated_at: string;
}

// EMO Avatar Component using Lottie
const EmoAvatar = ({ src, isSelected, onClick }: { src: string; isSelected: boolean; onClick: () => void }) => {
  const [animationData, setAnimationData] = useState<any>(null);

  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch(src + `?t=${Date.now()}`);
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load animation:', error);
      }
    };

    loadAnimation();
  }, [src]);

  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };

  const { View } = useLottie(options);

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      style={{
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        border: isSelected ? '3px solid #0ea5e9' : '2px solid rgba(31, 42, 42, 0.1)',
        background: 'rgba(255, 255, 255, 0.8)',
        cursor: 'pointer',
        overflow: 'hidden',
        transition: 'all 0.2s ease',
      }}
    >
      {animationData ? (
        <div style={{ width: '100%', height: '100%' }}>
          {View}
        </div>
      ) : (
        <div style={{ width: '100%', height: '100%', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}></div>
      )}
    </motion.button>
  );
};

export const Profile = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [selectedEmo, setSelectedEmo] = useState('/Avatars/lottie.json');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [editFormData, setEditFormData] = useState({
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

  // Detect desktop vs mobile for content layout adjustment
  useEffect(() => {
    const checkDesktop = () => {
      setIsDesktop(window.innerWidth >= 768);
    };

    checkDesktop();
    window.addEventListener('resize', checkDesktop);
    return () => window.removeEventListener('resize', checkDesktop);
  }, []);

  const checkAuth = async () => {
    try {
      const res = await fetch('/auth/me', { credentials: 'include' });
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
      const response = await fetch('/api/profile', { credentials: 'same-origin' });
      if (!response.ok) return;
      const payload = await response.json();
      
      // Redirect to setup if no profile or incomplete setup
      if (!payload.has_profile || payload.is_setup_complete === false) {
        navigate('/setup');
        return;
      }
      
      if (payload.profile) {
        setProfileData(payload.profile);
        if (payload.profile.emo_avatar) {
          setSelectedEmo(payload.profile.emo_avatar);
        }
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
      setError('Failed to load profile data');
      // On error, also redirect to setup
      navigate('/setup');
    } finally {
      setLoading(false);
    }
  };

  const saveEmoSelection = async (emoPath: string) => {
    setSelectedEmo(emoPath);
    setSaving(true);
    
    try {
      const response = await fetch('/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ emo_avatar: emoPath }),
      });

      if (!response.ok) {
        throw new Error('Failed to save EMO selection');
      }

      if (profileData) {
        setProfileData({ ...profileData, emo_avatar: emoPath });
      }
    } catch (err) {
      console.error('Failed to save EMO:', err);
      setError('Failed to save EMO selection');
    } finally {
      setSaving(false);
    }
  };

  const openEditModal = () => {
    if (profileData) {
      setEditFormData({
        work_description: profileData.work_description || '',
        industry: profileData.industry || '',
        responsibilities: profileData.responsibilities || '',
        company_name: profileData.company_name || '',
        work_environment: profileData.work_environment || '',
      });
      setIsEditModalOpen(true);
    }
  };

  const closeEditModal = () => {
    setIsEditModalOpen(false);
    setError('');
  };

  const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setEditFormData(prev => ({ ...prev, [name]: value }));
  };

  const saveProfileChanges = async () => {
    setSaving(true);
    setError('');

    try {
      const response = await fetch('/api/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(editFormData),
      });

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({}));
        throw new Error(errorPayload.error || 'Failed to save profile changes');
      }

      // Refresh profile data
      const loadResponse = await fetch('/api/profile', { credentials: 'same-origin' });
      if (loadResponse.ok) {
        const payload = await loadResponse.json();
        if (payload.profile) {
          setProfileData(payload.profile);
        }
      }
      closeEditModal();
    } catch (err: any) {
      setError(err.message || 'Failed to save profile changes');
    } finally {
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

  if (loading) {
    return (
      <main style={{ minHeight: '100vh', background: '#F7F9FC', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '4px solid #E8F0FF',
            borderTop: '4px solid #0ea5e9',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#64748B' }}>Loading profile...</p>
        </div>
      </main>
    );
  }

  return (
    <main
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        background: '#F7F9FC',
        overflow: 'hidden',
        paddingBottom: '120px',
      }}
    >
      <AnimatedBackground accentColor="#6EB5FF" />
      <div className="film-grain" aria-hidden="true" />

      {/* Side Navigation */}
      <SideNav />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{
          position: 'relative',
          zIndex: 1,
          maxWidth: '1080px',
          margin: '0 auto',
          padding: '32px',
          width: '100%',
          marginLeft: isDesktop ? '80px' : '0',
        }}
      >
        {/* User Header Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" as Easing }}
          style={{
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(31, 42, 42, 0.09)',
            borderRadius: '24px',
            padding: '32px',
            marginBottom: '32px',
            display: 'flex',
            alignItems: 'center',
            gap: '24px',
            boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
          }}
        >
          {/* EMO Avatar */}
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #6EB5FF 0%, #8DC4FF 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}>
            <MainEmoAvatar src={selectedEmo} />
          </div>

          {/* User Info */}
          <div style={{ flex: 1 }}>
            <h1 style={{
              fontFamily: '"Space Grotesk", sans-serif',
              fontSize: '2rem',
              fontWeight: '700',
              letterSpacing: '-0.04em',
              color: '#14213D',
              marginBottom: '8px',
            }}>
              {profileData?.name || 'User'}
            </h1>
            <p style={{ color: '#64748B', fontSize: '1rem', marginBottom: '4px' }}>
              {profileData?.email}
            </p>
            <p style={{ color: '#0ea5e9', fontSize: '0.875rem', fontWeight: 600 }}>
              Member since {profileData?.updated_at ? new Date(profileData.updated_at).toLocaleDateString() : 'Recently'}
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={openEditModal}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)',
            }}
          >
            Edit Profile
          </motion.button>
        </motion.div>

        {/* EMO Selector */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.2 }}
          style={{
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(31, 42, 42, 0.09)',
            borderRadius: '24px',
            padding: '32px',
            marginBottom: '32px',
            textAlign: 'center',
            boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
          }}
        >
          <h2 style={{
            fontFamily: '"Space Grotesk", sans-serif',
            fontSize: '1.5rem',
            fontWeight: '700',
            letterSpacing: '-0.04em',
            color: '#14213D',
            marginBottom: '8px',
          }}>
            Choose Your EMO
          </h2>
          <p style={{ color: '#64748B', fontSize: '0.875rem', marginBottom: '16px' }}>
            Select your personal EMO avatar
          </p>
          {saving && <p style={{ color: '#0ea5e9', fontSize: '0.875rem', marginBottom: '12px' }}>Saving...</p>}
          {error && <p style={{ color: '#DC2626', fontSize: '0.875rem', marginBottom: '12px' }}>{error}</p>}
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            {['/Avatars/lottie.json', '/Avatars/lottie-2.json', '/Avatars/lottie-3.json', '/Avatars/lottie-5.json', '/Avatars/lottie-7.json'].map((emo) => (
              <EmoAvatar
                key={emo}
                src={emo}
                isSelected={selectedEmo === emo}
                onClick={() => saveEmoSelection(emo)}
              />
            ))}
          </div>
        </motion.div>

        {/* Profile Cards Grid - keep the rest the same */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '24px',
        }}>
          {/* Keep your existing cards here... */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.3 }}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(31, 42, 42, 0.09)',
              borderRadius: '24px',
              padding: '28px',
              boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
            }}
          >
            <h3 style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#0ea5e9',
              marginBottom: '16px',
            }}>
              Work Information
            </h3>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Work Description</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.work_description || 'Not set'}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Industry</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.industry || 'Not set'}
              </p>
            </div>
          </motion.div>

                 {/* Role Details Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.4 }}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(31, 42, 42, 0.09)',
              borderRadius: '24px',
              padding: '28px',
              boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
            }}
          >
            <h3 style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#0ea5e9',
              marginBottom: '16px',
            }}>
              Role Details
            </h3>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Responsibilities</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.responsibilities || 'Not set'}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Company</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.company_name || 'Not set'}
              </p>
            </div>
          </motion.div>

          {/* Work Environment Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.5 }}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(31, 42, 42, 0.09)',
              borderRadius: '24px',
              padding: '28px',
              boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
            }}
          >
            <h3 style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#0ea5e9',
              marginBottom: '16px',
            }}>
              Work Environment
            </h3>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(14, 165, 233, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
              }}>
                {profileData?.work_environment === 'Remote' ? '🏠' : 
                 profileData?.work_environment === 'Hybrid' ? '🏢' : 
                 profileData?.work_environment === 'Office' ? '🏢' : '❓'}
              </div>
              <div>
                <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                  {profileData?.work_environment || 'Not set'}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
                  Current work arrangement
                </p>
              </div>
            </div>
          </motion.div>

          {/* Account Info Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.6 }}
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(31, 42, 42, 0.09)',
              borderRadius: '24px',
              padding: '28px',
              boxShadow: '0 24px 80px rgba(20, 33, 61, 0.08)',
            }}
          >
            <h3 style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: '#0ea5e9',
              marginBottom: '16px',
            }}>
              Account Information
            </h3>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Email</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.email || 'Not set'}
              </p>
            </div>
            <div>
              <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '4px' }}>Member Since</p>
              <p style={{ fontSize: '1rem', color: '#14213D', fontWeight: 500 }}>
                {profileData?.updated_at ? new Date(profileData.updated_at).toLocaleDateString() : 'Recently'}
              </p>
            </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Edit Profile Modal */}
      <AnimatePresence>
        {isEditModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '20px',
            }}
            onClick={closeEditModal}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'white',
                borderRadius: '24px',
                padding: '32px',
                maxWidth: '500px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 24px 80px rgba(20, 33, 61, 0.2)',
              }}
            >
            <h2 style={{
              fontFamily: '"Space Grotesk", sans-serif',
              fontSize: '1.5rem',
              fontWeight: '700',
              letterSpacing: '-0.04em',
              color: '#14213D',
              marginBottom: '24px',
            }}>
              Edit Profile
            </h2>

            {error && (
              <div style={{
                padding: '12px 16px',
                background: '#FEE2E2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                color: '#DC2626',
                fontSize: '0.875rem',
                marginBottom: '16px',
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: '#14213D', fontWeight: 500 }}>
                  Work Description
                </label>
                <input
                  type="text"
                  name="work_description"
                  value={editFormData.work_description}
                  onChange={handleEditInputChange}
                  placeholder="e.g., Software Development, Construction, Healthcare"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #E8F0FF',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#0ea5e9'}
                  onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: '#14213D', fontWeight: 500 }}>
                  Industry
                </label>
                <input
                  type="text"
                  name="industry"
                  value={editFormData.industry}
                  onChange={handleEditInputChange}
                  placeholder="e.g., Technology, Healthcare, Finance"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #E8F0FF',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#0ea5e9'}
                  onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: '#14213D', fontWeight: 500 }}>
                  Responsibilities
                </label>
                <textarea
                  name="responsibilities"
                  value={editFormData.responsibilities}
                  onChange={handleEditInputChange}
                  placeholder="Briefly describe your daily tasks and responsibilities"
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
                  onFocus={(e) => e.target.style.borderColor = '#0ea5e9'}
                  onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: '#14213D', fontWeight: 500 }}>
                  Company Name
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={editFormData.company_name}
                  onChange={handleEditInputChange}
                  placeholder="Your company name"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #E8F0FF',
                    borderRadius: '12px',
                    fontSize: '1rem',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#0ea5e9'}
                  onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '8px', color: '#14213D', fontWeight: 500 }}>
                  Work Environment
                </label>
                <select
                  name="work_environment"
                  value={editFormData.work_environment}
                  onChange={handleEditInputChange}
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
                  onFocus={(e) => e.target.style.borderColor = '#0ea5e9'}
                  onBlur={(e) => e.target.style.borderColor = '#E8F0FF'}
                >
                  <option value="">Select work environment</option>
                  <option>Hybrid</option>
                  <option>Remote</option>
                  <option>Office</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <motion.button
                type="button"
                onClick={closeEditModal}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={saving}
                style={{
                  flex: 1,
                  padding: '14px',
                  border: '1px solid #E8F0FF',
                  borderRadius: '12px',
                  background: 'white',
                  color: '#14213D',
                  fontSize: '1rem',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.7 : 1,
                  transition: 'all 0.2s',
                }}
              >
                Cancel
              </motion.button>
              <motion.button
                type="button"
                onClick={saveProfileChanges}
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.98 }}
                disabled={saving}
                style={{
                  flex: 1,
                  padding: '14px',
                  border: 'none',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                  color: 'white',
                  fontSize: '1rem',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.7 : 1,
                  transition: 'all 0.2s',
                }}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
        )}
      </AnimatePresence>

      <ResponsiveNav />
    </main>
  );
};

// Helper component for main avatar display
const MainEmoAvatar = ({ src }: { src: string }) => {
  const [animationData, setAnimationData] = useState<any>(null);

  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch(src + `?t=${Date.now()}`);
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load animation:', error);
      }
    };

    loadAnimation();
  }, [src]);

  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };

  const { View } = useLottie(options);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      {animationData ? View : <div style={{ width: '100%', height: '100%', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}></div>}
    </div>
  );
};