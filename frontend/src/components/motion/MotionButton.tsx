import { motion, Easing } from 'framer-motion';
import { useState } from 'react';

interface MotionButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  className?: string;
}

export const MotionButton = ({ onClick, children, className = '' }: MotionButtonProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const buttonVariants = {
    rest: {
      scale: 1,
      boxShadow: '0 20px 45px rgba(15, 118, 110, 0.24)'
    },
    hover: {
      scale: 1.02,
      boxShadow: '0 24px 52px rgba(15, 118, 110, 0.28)',
      transition: {
        duration: 0.2,
        ease: "easeOut" as Easing
      }
    },
    tap: {
      scale: 0.98,
      boxShadow: '0 16px 40px rgba(15, 118, 110, 0.2)',
      transition: {
        duration: 0.1,
        ease: "easeOut" as Easing
      }
    }
  };

  const iconVariants = {
    rest: { rotate: 0 },
    hover: { 
      rotate: 10,
      transition: {
        duration: 0.3,
        ease: "easeOut" as Easing
      }
    }
  };

  return (
    <motion.button
      className={`signin-btn ${className}`}
      onClick={onClick}
      variants={buttonVariants}
      initial="rest"
      whileHover="hover"
      whileTap="tap"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      style={{
        width: '100%',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        border: '1px solid rgba(255, 255, 255, 0.22)',
        borderRadius: '18px',
        background: 'linear-gradient(135deg, var(--teal) 0%, var(--teal-deep) 100%)',
        color: 'white',
        font: 'inherit',
        fontWeight: 700,
        fontSize: '1rem',
        textDecoration: 'none',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Shimmer effect on hover */}
      <motion.div
        style={{
          position: 'absolute',
          top: 0,
          left: '-100%',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
          pointerEvents: 'none'
        }}
        animate={{
          left: isHovered ? '100%' : '-100%'
        }}
        transition={{
          duration: 0.6,
          ease: "easeInOut" as Easing
        }}
      />
      
      {/* Google icon with animation */}
      <motion.span 
        className="signin-icon google-icon" 
        aria-hidden="true"
        variants={iconVariants}
        animate={isHovered ? "hover" : "rest"}
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '999px',
          background: 'rgba(255, 255, 255, 0.16)',
          display: 'grid',
          placeItems: 'center',
          flex: '0 0 28px',
          boxShadow: 'inset 0 0 0 1px rgba(255, 255, 255, 0.08)'
        }}
      >
        <svg viewBox="0 0 24 24" width="16" height="16" style={{ display: 'block' }}>
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
      </motion.span>
      
      <motion.span
        animate={{
          x: isHovered ? 2 : 0
        }}
        transition={{
          duration: 0.2,
          ease: "easeOut" as Easing
        }}
      >
        {children}
      </motion.span>
    </motion.button>
  );
};