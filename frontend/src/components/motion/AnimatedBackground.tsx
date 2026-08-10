import { FloatingBlob } from './FloatingBlob';
import { ParticleField } from './ParticleField';

export const AnimatedBackground = () => {
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
          background: 'radial-gradient(circle, #BFD7FF 0%, rgba(191,215,255,0) 70%)',
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
          background: 'radial-gradient(circle, #DCE9FF 0%, rgba(220,233,255,0) 70%)',
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
          background: 'radial-gradient(circle, #A9C9FF 0%, rgba(169,201,255,0) 75%)',
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
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0) 70%)',
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
          background: 'radial-gradient(circle, rgba(245, 158, 11, 0.12) 0%, rgba(245, 158, 11, 0) 70%)',
        }}
        delay={1.5}
      />
      
      {/* Particle field */}
      <ParticleField />
    </>
  );
};