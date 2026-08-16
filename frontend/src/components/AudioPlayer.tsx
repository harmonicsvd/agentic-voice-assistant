interface AudioPlayerProps {
  audioRef: React.RefObject<HTMLAudioElement | null>;
}

export const AudioPlayer = ({ audioRef }: AudioPlayerProps) => {
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
