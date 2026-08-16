import { motion, Easing } from 'framer-motion';
import { useTypingAnimation } from '../../hooks/useTypingAnimation';
import { EmojiCarousel } from './EmojiCarousel';

// Typing animation component using custom hook
const TypingAnimation = () => {
  const firstPhrase = 'Your personal assistant';
  const finalPhrase = 'Your personal agentic voice assistant.';

  const { text, animationComplete } = useTypingAnimation({
    firstPhrase,
    finalPhrase,
    typingSpeed: 50,
    deletingSpeed: 30,
    pauseBeforeDelete: 1500,
    pauseAfterDelete: 300
  });

  return (
    <p
      style={{
        fontSize: 'clamp(1rem, 1.5vw, 1.5rem)',
        color: 'var(--text-soft)',
        marginTop: '20px',
        textAlign: 'center',
        opacity: 0.9,
        minHeight: '2rem'
      }}
    >
      {text}{!animationComplete && <span style={{ animation: 'blink 1s infinite' }}>|</span>}
    </p>
  );
};

// Old components removed - replaced with EmojiCarousel

export const EMOLogo = ({ onColorChange, compact = false }: { onColorChange?: (color: string) => void, compact?: boolean } = {}) => {
  // Container variants for main logo
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

  // Custom variants for each character's sliding animation with individual timing
  const eVariants = {
    hidden: { 
      opacity: 0,
      x: 0
    },
    visible: { 
      opacity: 1,
      x: -40,
      transition: {
        duration: 0.6,
        ease: "easeOut" as Easing,
        delay: 0.2
      }
    }
  };

  const mVariants = {
    hidden: { 
      opacity: 0,
      x: 0
    },
    visible: { 
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut" as Easing,
        delay: 0.8
      }
    }
  };

  const oVariants = {
    hidden: { 
      opacity: 0,
      x: 0
    },
    visible: { 
      opacity: 1,
      x: 40,
      transition: {
        duration: 0.6,
        ease: "easeOut" as Easing,
        delay: 1.4
      }
    }
  };

  // Label variants with delays after each character
  const eLabelVariants = {
    hidden: { 
      opacity: 0,
      y: 5
    },
    visible: { 
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut" as Easing,
        delay: 0.8 // After E appears
      }
    }
  };

  const mLabelVariants = {
    hidden: { 
      opacity: 0,
      y: 5
    },
    visible: { 
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut" as Easing,
        delay: 1.4 // After M appears
      }
    }
  };

  const oLabelVariants = {
    hidden: { 
      opacity: 0,
      y: 5
    },
    visible: { 
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut" as Easing,
        delay: 2.0 // After O appears
      }
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: compact ? 'flex-start' : 'center',
        marginBottom: compact ? '0' : '32px'
      }}
    >
      {/* EMO Brand Name - Split into individual characters with labels */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{
          display: 'flex',
          fontFamily: '"Space Grotesk", sans-serif',
          fontSize: compact ? '18vw' : 'clamp(10rem, 18vw, 20rem)',
          fontWeight: 700,
          letterSpacing: compact ? '0.1em' : '-0.04em',
          color: 'var(--text-main)',
          margin: 0,
          textAlign: 'center',
          position: 'relative',
        }}
      >
        {/* E with label */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center',marginRight: compact ? '20px' : '0' }}>
          <motion.span variants={eVariants}>E</motion.span>
          <motion.span 
            variants={eLabelVariants}
            style={{
              fontSize: compact ? '1.2rem' : 'clamp(1rem, 1.2vw, 1rem)',
              color: 'var(--text-soft)',
              marginTop: '-80px',
              textAlign: 'center',
              letterSpacing: '0.05em',
              opacity: 0.7,
              width: 'auto',
              maxWidth: compact ? '60px' : 'clamp(4rem, 8vw, 10rem)',
              marginLeft: compact ? '-80px' : '-80px'
            }}
          >
            expressive
          </motion.span>
        </div>

        {/* M with label */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <motion.span variants={mVariants}>M</motion.span>
          <motion.span 
            variants={mLabelVariants}
            style={{
              fontSize: compact ? '1.2rem' : 'clamp(0.6rem, 1.2vw, 1rem)',
              color: 'var(--text-soft)',
              marginTop: compact ? '-38px' : '-80px',
              textAlign: 'center',
              letterSpacing: '0.05em',
              opacity: 0.7,
              width: 'auto',
              maxWidth: compact ? '60px' : 'clamp(4rem, 8vw, 10rem)',
              marginLeft: compact ? '-47px' : '18px',
            }}
          >
            multimodal
          </motion.span>
        </div>

        {/* O with label */}
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginLeft: compact ? '-40px' : '0' }}>
          <motion.span variants={oVariants}>O</motion.span>
          <motion.span 
            variants={oLabelVariants}
            style={{
              fontSize: compact ? '1.2rem' : 'clamp(0.6rem, 1.2vw, 1rem)',
              color: 'var(--text-soft)',
              marginTop: compact ? '-38px' : '-80px',
              textAlign: 'center',
              letterSpacing: '0.05em',
              opacity: 0.7,
              width: 'auto',
              maxWidth: compact ? '60px' : 'clamp(4rem, 8vw, 10rem)',
              marginLeft: compact ? '60px' : '95px'
            }}
          >
            operator
          </motion.span>
        </div>
      </motion.div>

      {/* Only show emoji carousel and typing animation in non-compact mode */}
      {!compact && (
        <>
          {/* Emoji Carousel - Interactive 3D carousel */}
          <EmojiCarousel onColorChange={onColorChange} />

          {/* Typing Animation */}
          <TypingAnimation />
        </>
      )}
    </div>
  );
};