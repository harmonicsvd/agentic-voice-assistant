import { useState, useEffect, useMemo } from 'react';
import { useLottie } from 'lottie-react';
import React from 'react';

type VoiceEmojiState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'processing' | 'success' | 'error';

interface VoiceEmojiProps {
  state: VoiceEmojiState;
}

interface EmojiData {
  src: string;
  color: string;
  status: string;
}

const EMOJIS: EmojiData[] = [
  { 
    src: '/Avatars/lottie-5.json', 
    color: '#F59E0B', 
    status: 'Sleeping'
  },
  { 
    src: '/Avatars/lottie-2.json', 
    color: '#8B5CF6', 
    status: 'Listening'
  },
  { 
    src: '/Avatars/lottie.json', 
    color: '#6EB5FF', 
    status: 'Processing'
  },
  { 
    src: '/Avatars/lottie-3.json', 
    color: '#10B981', 
    status: 'Speaking'
  },
  { 
    src: '/Avatars/lottie-7.json', 
    color: '#EF4444', 
    status: 'Error'
  },
];

// Map state to emoji index
const STATE_TO_INDEX: Record<VoiceEmojiState, number> = {
  idle: 0,           // Sleeping
  listening: 1,      // Listening
  thinking: 2,       // Processing
  speaking: 3,       // Speaking
  processing: 2,     // Processing
  success: 3,        // Speaking (ready)
  error: 4,          // Error
};

interface CarouselRoles {
  center: number;
  left: number;
  right: number;
  back1: number;
  back2: number;
}

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
    return <div style={{ 
      width: '100%', 
      height: '100%', 
      background: 'rgba(255,255,255,0.1)', 
      borderRadius: '50%' 
    }}></div>;
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      {View}
    </div>
  );
};

export const VoiceEmoji = ({ state }: VoiceEmojiProps) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [imagesLoaded, setImagesLoaded] = useState(false);

  // Load all emojis on mount
  useEffect(() => {
    const loadAllEmojis = async () => {
      try {
        await Promise.all(EMOJIS.map(emoji => 
          fetch(emoji.src + `?t=${Date.now()}`).then(res => res.json())
        ));
        setImagesLoaded(true);
      } catch (error) {
        console.error('Failed to load emojis:', error);
        setImagesLoaded(true);
      }
    };
    loadAllEmojis();
  }, []);

  // Update carousel index when state changes (instead of time interval)
  useEffect(() => {
    const targetIndex = STATE_TO_INDEX[state] || 0;
    setActiveIndex(targetIndex);
  }, [state]);

  // Calculate roles based on activeIndex (same as login page)
  const roles = useMemo((): CarouselRoles => {
    const center = activeIndex;
    const left = (activeIndex + EMOJIS.length - 1) % EMOJIS.length;
    const right = (activeIndex + 1) % EMOJIS.length;
    const back1 = (activeIndex + 2) % EMOJIS.length;
    const back2 = (activeIndex + 3) % EMOJIS.length;
    return { center, left, right, back1, back2 };
  }, [activeIndex]);

  const getEmojiStyle = (index: number): React.CSSProperties => {
    const role = Object.keys(roles).find(key => roles[key as keyof CarouselRoles] === index);
    
    const baseStyle: React.CSSProperties = {
      position: 'absolute' as const,
      aspectRatio: '1 / 1',
      transition: 'transform 650ms cubic-bezier(0.4,0,0.2,1), filter 650ms cubic-bezier(0.4,0,0.2,1), opacity 650ms cubic-bezier(0.4,0,0.2,1), left 650ms cubic-bezier(0.4,0,0.2,1), bottom 650ms cubic-bezier(0.4,0,0.2,1)',
      willChange: 'transform, filter, opacity' as const,
    };

    const scaleFactor = 1;

    switch (role) {
      case 'center':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(1)',
          filter: 'none',
          opacity: 1,
          zIndex: 20,
          left: '50%',
          height: `${180 * scaleFactor}px`,
          bottom: '15%',
        };
      case 'left':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.7)',
          filter: 'blur(2px)',
          opacity: 0.7,
          zIndex: 10,
          left: '25%',
          height: `${120 * scaleFactor}px`,
          bottom: '18%',
        };
      case 'right':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.7)',
          filter: 'blur(2px)',
          opacity: 0.7,
          zIndex: 10,
          left: '75%',
          height: `${120 * scaleFactor}px`,
          bottom: '18%',
        };
      case 'back1':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.5)',
          filter: 'blur(4px)',
          opacity: 0.4,
          zIndex: 5,
          left: '50%',
          height: `${100 * scaleFactor}px`,
          bottom: '18%',
        };
      case 'back2':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.4)',
          filter: 'blur(6px)',
          opacity: 0.2,
          zIndex: 4,
          left: '50%',
          height: `${80 * scaleFactor}px`,
          bottom: '18%',
        };
      default:
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0)',
          opacity: 0,
          zIndex: 1,
        };
    }
  };

  if (!imagesLoaded) {
    return null; // Don't show loading spinner - let parent handle loading state
  }

  return (
    <div style={{ 
      width: '100%', 
      height: '280px',
      position: 'relative',
      margin: '0 auto'
    }}>
      {EMOJIS.map((emoji, index) => (
        <div key={index} style={getEmojiStyle(index)}>
          <LottieEmoji 
            src={emoji.src} 
            isLoaded={imagesLoaded} 
          />
        </div>
      ))}
    </div>
  );
};