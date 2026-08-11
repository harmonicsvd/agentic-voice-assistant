import { motion, Easing } from 'framer-motion';
import { useMemo } from 'react';

interface Particle {
  x: number;
  y: number;
  size: number;
  opacity: number;
  duration: number;
  delay: number;
}

interface ParticleFieldProps {
  accentColor?: string;
}

const hexToRgba = (hex: string, alpha: number) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

export const ParticleField = ({ accentColor = '#0ea5e9' }: ParticleFieldProps) => {
  const particles = useMemo(() => {
    const particleCount = 25;
    const newParticles: Particle[] = [];
    
    for (let i = 0; i < particleCount; i++) {
      newParticles.push({
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: 2 + Math.random() * 3,
        opacity: 0.1 + Math.random() * 0.2,
        duration: 10 + Math.random() * 15,
        delay: Math.random() * 5
      });
    }
    
    return newParticles;
  }, []);

  const particleVariants = {
    float: (custom: Particle) => ({
      x: [custom.x, custom.x + (Math.random() - 0.5) * 20, custom.x],
      y: [custom.y, custom.y + (Math.random() - 0.5) * 20, custom.y],
      opacity: [custom.opacity, custom.opacity * 0.5, custom.opacity],
      transition: {
        duration: custom.duration,
        repeat: Infinity,
        ease: "easeInOut" as Easing,
        delay: custom.delay
      }
    })
  };

  return (
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'hidden' }}>
      {particles.map((particle, index) => (
        <motion.div
          key={index}
          custom={particle}
          variants={particleVariants}
          animate="float"
          style={{
            position: 'absolute',
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: particle.size,
            height: particle.size,
            borderRadius: '50%',
            backgroundColor: hexToRgba(accentColor, 0.3),
            opacity: particle.opacity,
            transition: 'background-color 1.5s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      ))}
    </div>
  );
};