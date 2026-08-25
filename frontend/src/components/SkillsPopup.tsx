import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageSquare } from 'lucide-react';

import { installSkill, uninstallSkill, getAvailableSkills } from '../services/skillsApi';
import { useEffect, useState } from 'react'; // Add this import
 
import { GoogleCalendarIcon } from './GoogleCalendarIcon';

interface SkillsPopupProps {
  isOpen: boolean;
  onClose: () => void;
  position: { x: number; y: number };
}

const SKILL_DISPLAY_INFO = {
  'meeting_discussion': {
    name: 'Meeting Discussion',
    icon: <MessageSquare size={38} color="#0ea5e9" />,
    iconBg: 'rgba(14, 165, 233, 0.1)',
    iconBgRadius: '8px'
  },
  'google_calendar': {
    name: 'Google Calendar',
    icon: <GoogleCalendarIcon width="48" height="48" />,
    iconBg: 'transparent',
    iconBgRadius: '8px'
  },
  // Add more skills as they become available
};


export const SkillsPopup = ({ isOpen, onClose, position }: SkillsPopupProps) => {

const [installedSkills, setInstalledSkills] = useState<Set<string>>(new Set());
const [loading, setLoading] = useState(false);
const [installingSkill, setInstallingSkill] = useState<string | null>(null);
const [installProgress, setInstallProgress] = useState(0);



useEffect(() => {
  if (isOpen) {
    fetchInstalledSkills();
  }
}, [isOpen]);

const fetchInstalledSkills = async () => {
  setLoading(true);
  try {
    const data = await getAvailableSkills();
    const installed = new Set(
      data.available_skills
        .filter((skill: { skill_name: string, installed: boolean }) => skill.installed)
        .map((skill: { skill_name: string }) => skill.skill_name)
    );
    setInstalledSkills(installed);
  } catch (error) {
    console.error('Failed to fetch skills:', error);
  } finally {
    setLoading(false);
  }
};

const handleInstallToggle = async (skillName: string, isInstalled: boolean) => {
  setInstallingSkill(skillName);
  setInstallProgress(0);
  
  try {
    // Simulate progress
    const progressInterval = setInterval(() => {
      setInstallProgress(prev => Math.min(prev + 20, 90));
    }, 200);
    
    if (isInstalled) {
      await uninstallSkill(skillName);
    } else {
      await installSkill(skillName);
    }
    
    clearInterval(progressInterval);
    setInstallProgress(100);
    
   // Small delay to show 100% before updating
    setTimeout(() => {
      // Update local state directly instead of fetching
      setInstalledSkills(prev => {
        const newSet = new Set(prev);
        if (isInstalled) {
          newSet.delete(skillName);
        } else {
          newSet.add(skillName);
        }
        return newSet;
      });
      setInstallingSkill(null);
      setInstallProgress(0);
    }, 500);
  } catch (error) {
    console.error('Failed to toggle skill installation:', error);
    setInstallingSkill(null);
    setInstallProgress(0);
  }
};


  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop/Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.3)',
              zIndex: 998,
            }}
          />
          
          {/* Popup Panel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, x: -20 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.9, x: -20 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 25,
            }}
            style={{
              position: 'fixed',
              left: position.x + 60, // Offset from sidebar
              top: position.y,
              width: '600px',
              maxHeight: '700px',
              background: 'rgba(255, 255, 255, 0.95)',
              backdropFilter: 'blur(16px)',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '24px',
              boxShadow: '0 24px 80px rgba(20, 33, 61, 0.15)',
              zIndex: 999,
              overflow: 'hidden',
            }}
          >
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '20px 24px',
              borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
            }}>
              <h2 style={{
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#14213D',
                margin: 0,
              }}>
                Skills
              </h2>
              <button
                onClick={onClose}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'rgba(0, 0, 0, 0.05)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(0, 0, 0, 0.1)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)'}
              >
                <X size={18} color="#14213D" />
              </button>
            </div>

           {/* Skills Grid */}
<div style={{
  padding: '24px',
  display: 'grid',
  gridTemplateColumns: 'repeat(3, 1fr)',
  gap: '20px',
}}>
  {loading ? (
    <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
      Loading skills...
    </div>
  ) : (
    <>
      {Object.entries(SKILL_DISPLAY_INFO).map(([skillKey, displayInfo]) => {
        const isInstalled = installedSkills.has(skillKey);
        
        return (
          <motion.div
            key={skillKey}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              padding: '16px',
              borderRadius: '12px',
              border: '1px solid rgba(0, 0, 0, 0.05)',
              background: 'rgba(255, 255, 255, 0.5)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{
              width: '48px',
              height: '48px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: displayInfo.iconBg,
              borderRadius: displayInfo.iconBgRadius,
            }}>
              {displayInfo.icon}
            </div>
            <span style={{
              fontFamily: '"Space Grotesk", sans-serif',
              fontSize: '0.85rem',
              fontWeight: 600,
              color: '#14213D',
              textAlign: 'center',
            }}>
              {displayInfo.name}
            </span>
            <button
              onClick={() => handleInstallToggle(skillKey, isInstalled)}
              disabled={installingSkill === skillKey}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid rgba(20, 33, 61, 0.2)',
                background: isInstalled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(255, 255, 255, 0.8)',
                color: isInstalled ? '#16a34a' : '#14213D',
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: '0.75rem',
                fontWeight: 500,
                cursor: installingSkill === skillKey ? 'not-allowed' : 'pointer',
                opacity: installingSkill === skillKey ? 0.6 : 1,
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                if (installingSkill !== skillKey) {
                  e.currentTarget.style.background = isInstalled ? 'rgba(34, 197, 94, 0.2)' : 'rgba(20, 33, 61, 0.05)';
                }
              }}
              onMouseLeave={(e) => {
                if (installingSkill !== skillKey) {
                  e.currentTarget.style.background = isInstalled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(255, 255, 255, 0.8)';
                }
              }}
            >
              {installingSkill === skillKey ? (isInstalled ? 'Uninstalling...' : 'Installing...') : (isInstalled ? 'Installed' : 'Install')}
            </button>


            {installingSkill === skillKey && (
                    <div style={{
                      position: 'absolute',
                      bottom: '0',
                      left: '0',
                      right: '0',
                      height: '4px',
                      background: 'rgba(0,0,0,0.1)',
                      borderRadius: '0 0 12px 12px',
                      overflow: 'hidden',
                    }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${installProgress}%` }}
                        transition={{ duration: 0.2 }}
                        style={{
                          height: '100%',
                          background: '#0ea5e9',
                        }}
                      />
                    </div>
                  )}
          </motion.div>
        );
      })}
      
            {/* Keep the "More Skills Coming" placeholder */}
      <motion.div
        whileHover={{ scale: 1.05 }}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
          padding: '16px',
          borderRadius: '12px',
          border: '2px dashed rgba(0, 0, 0, 0.1)',
          background: 'rgba(0, 0, 0, 0.02)',
          cursor: 'default',
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{
          width: '48px',
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(99, 102, 241, 0.1)',
          borderRadius: '8px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
          }}>
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#6366f1',
              animation: 'pulse 1.5s ease-in-out infinite',
            }} />
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#6366f1',
              animation: 'pulse 1.5s ease-in-out infinite 0.3s',
            }} />
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#6366f1',
              animation: 'pulse 1.5s ease-in-out infinite 0.6s',
            }} />
          </div>
        </div>
        <span style={{
          fontFamily: '"Space Grotesk", sans-serif',
          fontSize: '0.8rem',
          fontWeight: 500,
          color: '#6366f1',
          textAlign: 'center',
        }}>
          More Skills Coming Soon...
        </span>
      </motion.div>
    </>
  )}
</div>
            {/* Add CSS for pulse animation */}
            <style>{`
              @keyframes pulse {
                0%, 100% { opacity: 0.4; transform: scale(1); }
                50% { opacity: 1; transform: scale(1.2); }
              }
            `}</style>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};