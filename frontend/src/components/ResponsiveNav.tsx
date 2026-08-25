import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, User, LogOut } from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  action?: 'logout';
}

export const ResponsiveNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobile, setIsMobile] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const dockRef = useRef<HTMLDivElement>(null);

  // Navigation items configuration
  const navItems: NavItem[] = [
    {
      id: 'home',
      label: 'Home',
      icon: <Home size={20} />,
      path: '/assistant',
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: <User size={20} />,
      path: '/profile',
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: <LogOut size={20} />,
      path: '/login',
      action: 'logout',
    },
  ];

  // Check if current path matches nav item (more specific matching)
  const isActive = (item: NavItem) => {
    if (item.action === 'logout') return false;
    
    return location.pathname === item.path;
  };

  // Handle navigation click
  const handleNavClick = async (item: NavItem) => {
    if (item.action === 'logout') {
      try {
        await fetch('/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });
      } catch (error) {
        console.error('Logout error:', error);
      } finally {
        navigate('/login');
      }
    } else {
      navigate(item.path);
    }
  };

  // Track mouse position relative to dock
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!dockRef.current) return;
    const rect = dockRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  // Calculate scale based on cursor proximity (smooth interpolation)
  const calculateScale = (itemIndex: number) => {
    if (isMobile) return 1;
    
    const itemWidth = 80; // Wider for text labels
    const gap = 12;
    const itemCenterX = itemIndex * (itemWidth + gap) + itemWidth / 2;
    
    const distance = Math.abs(mousePosition.x - itemCenterX);
    const maxDistance = 100; // Reduced since we have fewer items
    
    // Smooth proximity function
    const proximity = Math.max(0, 1 - distance / maxDistance);
    
    return 1 + proximity * 0.15; // Scale from 1.00 to 1.15 (very subtle)
  };

  // Responsive detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 640);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Desktop/Tablet - Text-based Navigation with EMO typography
  if (!isMobile) {
    return (
      <div style={{ position: 'fixed', left: '0', right: '0', bottom: '24px', display: 'flex', justifyContent: 'center', marginRight:'-88px', zIndex: 1000 }}>
        <motion.div
          ref={dockRef}
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ 
            type: "spring",
            stiffness: 300,
            damping: 25,
            delay: 0.2
          }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setMousePosition({ x: 0, y: 0 })}
          style={{
            background: 'rgba(255, 255, 255, 0.25)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '24px',
            boxShadow: '0 8px 32px rgba(20, 33, 61, 0.06)',
            display: 'flex',
            gap: '12px',
            padding: '12px 20px',
          }}
        >

        {navItems.map((item, index) => {
          const scale = calculateScale(index);
          
          return (
            <motion.button
              key={item.id}
              onClick={() => handleNavClick(item)}
              className={item.id === 'profile' ? 'profile-button' : ''}
              style={{
                padding: '10px 20px',
                borderRadius: '16px',
                border: 'none',
                background: isActive(item)
                  ? 'rgba(14, 165, 233, 0.12)'
                  : 'transparent',
                color: isActive(item) ? '#0ea5e9' : '#14213D',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.95rem',
                fontWeight: 700,
                transition: 'all 0.2s ease',
                transformOrigin: '50% 100%',
                fontFamily: '"Space Grotesk", sans-serif',
                letterSpacing: '-0.03em',
              }}
              animate={{
                scale,
              }}
              transition={{
                type: "spring",
                stiffness: 400,
                damping: 25,
                mass: 0.4,
              }}
              whileTap={{ scale: 0.95 }}
            >
              {item.label}
            </motion.button>
          );
        })}
        </motion.div>
      </div>
    );
  }

  // Mobile - Icon-based Navigation with EMO styling
  return (
    <div style={{ position: 'fixed', left: '0', right: '0', bottom: '16px', display: 'flex', justifyContent: 'center', zIndex: 1000 }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ 
          type: "spring",
          stiffness: 300,
          damping: 25,
          delay: 0.2
        }}
        style={{
          background: 'rgba(255, 255, 255, 0.35)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '20px',
          boxShadow: '0 8px 32px rgba(20, 33, 61, 0.06)',
          display: 'flex',
          justifyContent: 'space-around',
          padding: '10px 12px',
          paddingBottom: 'max(10px, env(safe-area-inset-bottom) + 10px)',
          margin: '0 16px',
        }}
      >
      {navItems.map((item) => (
        <motion.button
          key={item.id}
          onClick={() => handleNavClick(item)}
          className={item.id === 'profile' ? 'profile-button' : ''}
          whileTap={{ scale: 0.9 }}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '4px',
            padding: '8px 12px',
            borderRadius: '12px',
            border: 'none',
            background: 'transparent',
            color: isActive(item) ? '#0ea5e9' : '#14213D',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            minWidth: '44px',
          }}
        >
          <motion.div
            animate={{
              scale: isActive(item) ? 1.1 : 1,
            }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            {item.icon}
          </motion.div>
          
          {/* Active indicator */}
          {isActive(item) && (
            <motion.div
              layoutId="activeIndicator"
              transition={{
                type: "spring",
                stiffness: 500,
                damping: 30,
              }}
              style={{
                width: '3px',
                height: '3px',
                background: '#0ea5e9',
                borderRadius: '50%',
                boxShadow: '0 0 6px rgba(14, 165, 233, 0.6)',
              }}
            />
          )}
        </motion.button>
      ))}
      </motion.div>
    </div>
  );
};