import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { FileText, Wrench } from 'lucide-react';
import { SkillsPopup } from './SkillsPopup';

interface SideNavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  hidden?: boolean;
}

export const SideNav = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isSkillsPopupOpen, setIsSkillsPopupOpen] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const skillsButtonRef = useRef<HTMLButtonElement>(null);

  // Side navigation items configuration
  const sideNavItems: SideNavItem[] = [
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={20} />,
      path: '/documents',
      hidden: true, 
    },
    {
      id: 'skills',
      label: 'Skills',
      icon: <Wrench size={20} />,
      path: '/assistant', // Will navigate to assistant until skills page exists
    },
  ];

  // Handle navigation click
  const handleNavClick = (item: SideNavItem) => {
  if (item.id === 'skills') {
    // Open skills popup
    if (skillsButtonRef.current) {
      const rect = skillsButtonRef.current.getBoundingClientRect();
      setPopupPosition({ x: rect.left, y: rect.top });
    }
    setIsSkillsPopupOpen(true);
  } else {
    // Other items are still disabled
    console.log(`${item.label} navigation is currently disabled`);
  }
};
  // Responsive detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Desktop/Tablet - Left sidebar navigation (icons only with tooltips)
  // Only show on desktop since functionality is disabled
  if (isMobile) {
    return null;
  }
  return (
  <>
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ 
        type: "spring",
        stiffness: 300,
        damping: 25,
        delay: 0.1
      }}
      style={{
        position: 'fixed',
        left: '24px',
        top: '40%',
        transform: 'translateY(-50%)',
        background: 'rgba(255, 255, 255, 0.25)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '24px',
        boxShadow: '0 8px 32px rgba(20, 33, 61, 0.06)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '16px',
        zIndex: 100,
      }}
    >
      {sideNavItems.filter(item => !item.hidden).map((item) => (
        <motion.button
          key={item.id}
          ref={item.id === 'skills' ? skillsButtonRef : null}
          onClick={() => handleNavClick(item)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className={item.id === 'skills' ? 'skills-button' : ''}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '12px',
            borderRadius: '16px',
            border: 'none',
            background: 'transparent',
            color: '#14213D',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            minWidth: '44px',
            minHeight: '44px',
            opacity: 0.6,
          }}
          title={item.label}
        >
          {item.icon}
        </motion.button>
      ))}
    </motion.div>
    
    <SkillsPopup
      isOpen={isSkillsPopupOpen}
      onClose={() => setIsSkillsPopupOpen(false)}
      position={popupPosition}
    />
  </>
);
};