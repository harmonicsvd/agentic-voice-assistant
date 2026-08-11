import { FloatingBlob } from './FloatingBlob';
import { ParticleField } from './ParticleField';

interface AnimatedBackgroundProps {
  accentColor?: string;
}

export const AnimatedBackground = ({ accentColor = '#BFD7FF' }: AnimatedBackgroundProps) => {
  // Convert hex to rgba for gradient
  const hexToRgba = (hex: string, alpha: number) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  return (
    <>
      {/* Existing gradient blobs with animation */}
      <FloatingBlob
        style={{
          position: 'absolute',
          top: '-120px',
          left: '-100px',
          width: '420px',
          height: '420px',
          background: `radial-gradient(circle, ${accentColor} 0%, ${hexToRgba(accentColor, 0)} 70%)`,
          transition: 'background 1.5s cubic-bezier(0.4,0,0.2,1)',
        }}
        delay={0}
      />
      <FloatingBlob
        style={{
          position: 'absolute',
          bottom: '-140px',
          right: '-120px',
          width: '480px',
          height: '480px',
          background: `radial-gradient(circle, ${hexToRgba(accentColor, 0.7)} 0%, ${hexToRgba(accentColor, 0)} 70%)`,
          transition: 'background 1.5s cubic-bezier(0.4,0,0.2,1)',
        }}
        delay={1}
      />
      <FloatingBlob
        style={{
          position: 'absolute',
          top: '35%',
          right: '8%',
          width: '220px',
          height: '220px',
          background: `radial-gradient(circle, ${hexToRgba(accentColor, 0.8)} 0%, ${hexToRgba(accentColor, 0)} 75%)`,
          transition: 'background 1.5s cubic-bezier(0.4,0,0.2,1)',
        }}
        delay={2}
      />
      
      {/* Accent color blobs */}
      <FloatingBlob
        style={{
          position: 'absolute',
          top: '15%',
          left: '5%',
          width: '180px',
          height: '180px',
          background: `radial-gradient(circle, ${hexToRgba(accentColor, 0.3)} 0%, ${hexToRgba(accentColor, 0)} 70%)`,
          transition: 'background 1.5s cubic-bezier(0.4,0,0.2,1)',
        }}
        delay={0.5}
      />
      <FloatingBlob
        style={{
          position: 'absolute',
          bottom: '20%',
          left: '15%',
          width: '150px',
          height: '150px',
          background: `radial-gradient(circle, ${hexToRgba(accentColor, 0.25)} 0%, ${hexToRgba(accentColor, 0)} 70%)`,
          transition: 'background 1.5s cubic-bezier(0.4,0,0.2,1)',
        }}
        delay={1.5}
      />
      
      {/* Particle field */}
      <ParticleField accentColor={accentColor} />
    </>
  );
};