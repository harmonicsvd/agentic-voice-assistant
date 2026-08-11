import { useState, useEffect, useMemo } from 'react';

interface EmojiData {
  src: string;
  bg: string;
  panel: string;
}

interface UseEmojiCarouselOptions {
  emojis: EmojiData[];
  interval?: number;
  onColorChange?: (color: string) => void;
  compact?: boolean; // Add compact mode for smaller displays
  scale?: number; // Custom scale factor
}

interface CarouselRoles {
  center: number;
  left: number;
  right: number;
  back1: number;
  back2: number;
}

export const useEmojiCarousel = ({ 
  emojis, 
  interval = 4000, 
  onColorChange,
  compact = false,
  scale = 1
}: UseEmojiCarouselOptions) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [imagesLoaded, setImagesLoaded] = useState(false);

  // Handle mobile detection
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Preload all Lottie animations
  useEffect(() => {
    const loadAllAnimations = async () => {
      try {
        await Promise.all(
          emojis.map(emoji => fetch(emoji.src + `?t=${Date.now()}`).then(res => res.json()))
        );
        setImagesLoaded(true);
      } catch (error) {
        console.error('Failed to preload animations:', error);
        setImagesLoaded(true); // Proceed anyway
      }
    };
    loadAllAnimations();
  }, [emojis]);

  // Auto-rotate emojis
  useEffect(() => {
    const intervalId = setInterval(() => {
      if (!isAnimating) {
        setIsAnimating(true);
        setActiveIndex(prev => (prev + 1) % emojis.length);
        setTimeout(() => setIsAnimating(false), 1500);
      }
    }, interval);

    return () => clearInterval(intervalId);
  }, [isAnimating, interval, emojis.length]);

  // Notify parent of color changes
  useEffect(() => {
    if (onColorChange) {
      onColorChange(emojis[activeIndex].bg);
    }
  }, [activeIndex, onColorChange, emojis]);

  // Calculate roles based on activeIndex
  const roles = useMemo((): CarouselRoles => {
    const center = activeIndex;
    const left = (activeIndex + emojis.length - 1) % emojis.length;
    const right = (activeIndex + 1) % emojis.length;
    const back1 = (activeIndex + 2) % emojis.length;
    const back2 = (activeIndex + 3) % emojis.length;
    return { center, left, right, back1, back2 };
  }, [activeIndex, emojis.length]);

  const getEmojiStyle = (index: number) => {
    const role = Object.keys(roles).find(key => roles[key as keyof CarouselRoles] === index);
    
    const baseStyle: React.CSSProperties = {
      position: 'absolute',
      aspectRatio: '1 / 1',
      transition: 'transform 650ms cubic-bezier(0.4,0,0.2,1), filter 650ms cubic-bezier(0.4,0,0.2,1), opacity 650ms cubic-bezier(0.4,0,0.2,1), left 650ms cubic-bezier(0.4,0,0.2,1), bottom 650ms cubic-bezier(0.4,0,0.2,1)',
      willChange: 'transform, filter, opacity' as const,
    };

    // Use custom scale or compact mode scale
    const scaleFactor = compact ? 0.5 : scale;

    switch (role) {
      case 'center':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(1)',
          filter: 'none',
          opacity: 1,
          zIndex: 20,
          left: '50%',
          height: isMobile ? `${120 * scaleFactor}px` : `${180 * scaleFactor}px`,
          bottom: isMobile ? '20%' : '15%',
        };
      case 'left':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.7)',
          filter: 'blur(2px)',
          opacity: 0.7,
          zIndex: 10,
          left: isMobile ? '25%' : '30%',
          height: isMobile ? `${80 * scaleFactor}px` : `${120 * scaleFactor}px`,
          bottom: isMobile ? '25%' : '18%',
        };
      case 'right':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.7)',
          filter: 'blur(2px)',
          opacity: 0.7,
          zIndex: 10,
          left: isMobile ? '75%' : '70%',
          height: isMobile ? `${80 * scaleFactor}px` : `${120 * scaleFactor}px`,
          bottom: isMobile ? '25%' : '18%',
        };
      case 'back1':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.5)',
          filter: 'blur(4px)',
          opacity: 0.4,
          zIndex: 5,
          left: '50%',
          height: isMobile ? `${60 * scaleFactor}px` : `${100 * scaleFactor}px`,
          bottom: isMobile ? '25%' : '18%',
        };
      case 'back2':
        return {
          ...baseStyle,
          transform: 'translateX(-50%) scale(0.4)',
          filter: 'blur(6px)',
          opacity: 0.2,
          zIndex: 4,
          left: '50%',
          height: isMobile ? `${50 * scaleFactor}px` : `${80 * scaleFactor}px`,
          bottom: isMobile ? '25%' : '18%',
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

  return {
    activeIndex,
    isAnimating,
    isMobile,
    imagesLoaded,
    roles,
    getEmojiStyle,
    setActiveIndex,
  };
};