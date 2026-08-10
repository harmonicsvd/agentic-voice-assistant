import React, { useState, useEffect } from 'react';
import { useLottie } from 'lottie-react';

interface LottieCharacterProps {
  state?: 'idle' | 'listening' | 'thinking' | 'speaking' | 'processing' | 'success' | 'error';
}

const LottieCharacter: React.FC<LottieCharacterProps> = ({ state = 'idle' }) => {
  const [animationData, setAnimationData] = useState<any>(null);

  useEffect(() => {
    const loadAnimation = async () => {
      // Clear previous animation to prevent showing wrong state
      setAnimationData(null);

      let animationFile;
      switch (state) {
        case 'idle':
          animationFile = '/Avatars/lottie-5.json'; // Sleeping face - Z's floating
          break;
        case 'listening':
          animationFile = '/Avatars/lottie.json'; // Face with monocle - attentive, ready
          break;
        case 'thinking':
          animationFile = '/Avatars/lottie-2.json'; // Thinking face - hand on chin (user speaking)
          break;
        case 'processing':
          animationFile = '/Avatars/lottie.json'; // Face with monocle - bot searching
          break;
        case 'speaking':
          animationFile = '/Avatars/lottie-3.json'; // Grinning face - happy, engaged
          break;
        case 'success':
          animationFile = '/Avatars/lottie-3.json'; // Grinning face - happy
          break;
        case 'error':
          animationFile = '/Avatars/lottie-7.json'; // Spiral eyes - confused/error
          break;
        default:
          animationFile = '/Avatars/lottie-5.json'; // Sleeping face - default
      }

      try {
        const response = await fetch(animationFile + `?t=${Date.now()}`); // Add timestamp to prevent caching
        const data = await response.json();
        setAnimationData(data);
      } catch (error) {
        console.error('Failed to load animation:', error);
      }
    };

    loadAnimation();
  }, [state]);

  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };

  const { View } = useLottie(options);

  if (!animationData) {
    return <div style={{ width: '200px', height: '200px' }}>Loading...</div>;
  }

  return (
    <div style={{ width: '200px', height: '200px' }}>
      {View}
    </div>
  );
};

export default LottieCharacter;