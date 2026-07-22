import { useRef, useEffect } from 'react';

interface AudioPlayerProps {
  audioUrl: string | null;
  audioRef: React.RefObject<HTMLAudioElement | null>;
}

export const AudioPlayer = ({ audioUrl, audioRef }: AudioPlayerProps) => {
  return (
    <div style={{ marginTop: '20px' }}>
      <audio
        ref={audioRef}
        controls
        style={{ width: '100%' }}
      />
    </div>
  );
};
