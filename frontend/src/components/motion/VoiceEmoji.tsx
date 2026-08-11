import { useState, useEffect } from 'react';
import { useLottie } from 'lottie-react';

type VoiceEmojiState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'processing' | 'success' | 'error';

interface VoiceEmojiProps {
  state: VoiceEmojiState;
  onColorChange?: (color: string) => void;
}

interface EmojiMapping {
  src: string;
  color: string;
  status: string;
}

const EMOJI_MAPPING: Record<VoiceEmojiState, EmojiMapping> = {
  idle: {
    src: '/Avatars/lottie-5.json',
    color: '#F59E0B',
    status: 'Sleeping'
  },
  listening: {
    src: '/Avatars/lottie-2.json',
    color: '#6EB5FF',
    status: 'Listening'
  },
  thinking: {
    src: '/Avatars/lottie-2.json',
    color: '#8B5CF6',
    status: 'Thinking'
  },
  speaking: {
    src: '/Avatars/lottie-3.json',
    color: '#10B981',
    status: 'Speaking'
  },
  processing: {
    src: '/Avatars/lottie.json',
    color: '#8B5CF6',
    status: 'Processing'
  },
  success: {
    src: '/Avatars/lottie-3.json',
    color: '#10B981',
    status: 'Ready'
  },
  error: {
    src: '/Avatars/lottie-7.json',
    color: '#EF4444',
    status: 'Error'
  },
};

export const VoiceEmoji = ({ state, onColorChange }: VoiceEmojiProps) => {
  const [animationData, setAnimationData] = useState<any>(null);
  const currentEmoji = EMOJI_MAPPING[state] || EMOJI_MAPPING.idle;

  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch(currentEmoji.src + `?t=${Date.now()}`);
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load animation:', error);
      }
    };

    loadAnimation();
  }, [currentEmoji.src]);

  // Notify parent of color changes
  useEffect(() => {
    if (onColorChange) {
      onColorChange(currentEmoji.color);
    }
  }, [currentEmoji.color, onColorChange]);

  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };
  const { View } = useLottie(options);

  if (!animationData) {
    return (
      <div style={{ 
        width: '200px', 
        height: '200px',
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid rgba(14, 165, 233, 0.3)',
          borderTop: '4px solid #0ea5e9',
          borderRadius: '50%',
        }}></div>
      </div>
    );
  }

  return (
    <div style={{ width: '200px', height: '200px' }}>
      {View}
    </div>
  );
};