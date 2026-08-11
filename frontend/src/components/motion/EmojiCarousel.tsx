import { useState, useEffect } from 'react';
import { useLottie } from 'lottie-react';
import { useEmojiCarousel } from '../../hooks/useEmojiCarousel';

interface EmojiData {
  src: string;
  bg: string;
  panel: string;
}

interface EmojiCarouselProps {
  onColorChange?: (color: string) => void;
  compact?: boolean;
}

const EMOJIS: EmojiData[] = [
  { 
    src: '/Avatars/lottie.json', 
    bg: '#6EB5FF', 
    panel: '#8DC4FF'
  },
  { 
    src: '/Avatars/lottie-2.json', 
    bg: '#8B5CF6', 
    panel: '#A78BFA'
  },
  { 
    src: '/Avatars/lottie-3.json', 
    bg: '#10B981', 
    panel: '#34D399'
  },
  { 
    src: '/Avatars/lottie-5.json', 
    bg: '#F59E0B', 
    panel: '#FBBF24'
  },
  { 
    src: '/Avatars/lottie-7.json', 
    bg: '#EF4444', 
    panel: '#F87171'
  },
];

interface LottieEmojiProps {
  src: string;
  isLoaded: boolean;
}

const LottieEmoji = ({ src, isLoaded }: LottieEmojiProps) => {
  const [animationData, setAnimationData] = useState<any>(null);

  useEffect(() => {
    const loadAnimation = async () => {
      try {
        const response = await fetch(src + `?t=${Date.now()}`);
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load animation:', error);
      }
    };

    if (isLoaded) {
      loadAnimation();
    }
  }, [src, isLoaded]);

  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };
  const { View } = useLottie(options);

  if (!animationData) {
    return <div style={{ width: '100%', height: '100%', background: 'rgba(255,255,255,0.1)', borderRadius: '50%' }}></div>;
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      {View}
    </div>
  );
};

export const EmojiCarousel = ({ onColorChange, compact = false }: EmojiCarouselProps) => {
  const { isMobile, imagesLoaded, getEmojiStyle } = useEmojiCarousel({
    emojis: EMOJIS,
    interval: 4000,
    onColorChange,
    compact
  });

  return (
    <div 
      style={{
        position: 'relative',
        width: '100%',
        height: isMobile ? '200px' : '280px',
        overflow: 'visible',
        marginTop: '20px',
      }}
    >
      {/* Carousel */}
      <div style={{ position: 'relative', width: '100%', height: '100%' }}>
        {EMOJIS.map((emoji, index) => (
          <div key={index} style={getEmojiStyle(index)}>
            <LottieEmoji src={emoji.src} isLoaded={imagesLoaded} />
          </div>
        ))}
      </div>
    </div>
  );
};