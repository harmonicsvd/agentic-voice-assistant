import { motion, Easing } from 'framer-motion';

interface FloatingBlobProps {
  style?: React.CSSProperties;
  delay?: number;
  color?: string;
}

export const FloatingBlob = ({ style, delay = 0, color }: FloatingBlobProps) => {
  const blobVariants = {
    float: {
      x: [0, 30, -20, 0],
      y: [0, -25, 15, 0],
      scale: [1, 1.05, 0.98, 1],
      transition: {
        duration: 8 + Math.random() * 4,
        repeat: Infinity,
        ease: "easeInOut" as Easing,
        delay
      }
    }
  };

  const defaultStyle = {
    borderRadius: '50%',
    filter: 'blur(10px)',
    pointerEvents: 'none' as const,
    backgroundColor: color || 'rgba(110, 181, 255, 0.3)',
    ...style
  };

  return (
    <motion.div
      style={defaultStyle}
      variants={blobVariants}
      animate="float"
    />
  );
};