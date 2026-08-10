import { motion, Easing } from 'framer-motion';
import { AnimatedBackground } from '../components/motion/AnimatedBackground';
import { EMOLogo } from '../components/motion/EMOLogo';
import { MotionButton } from '../components/motion/MotionButton';

export const Login = () => {
  const handleLogin = () => {
    // Call actual Google OAuth endpoint - proxied through Vite
    window.location.href = '/auth/google/login';
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

  return (
    <main
      className="page"
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '24px',
        background: '#F7F9FC',
        overflow: 'hidden',
      }}
    >
      {/* Animated background with floating blobs and particles */}
      <AnimatedBackground />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{
          position: 'relative',
          zIndex: 1,
          width: '100%',
          maxWidth: '480px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          marginTop: '-60px'
        }}
      >
        {/* EMO Logo with animation */}
        <EMOLogo />

        {/* Enhanced Google OAuth button with micro-interactions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" as Easing, delay: 0.5 }}
        >
          <MotionButton onClick={handleLogin}>
            Continue with Google
          </MotionButton>
        </motion.div>
      </motion.div>
      
      {/* Film grain overlay */}
      <div className="film-grain" aria-hidden="true" />
    </main>
  );
};
