import React, { useState, useEffect } from 'react';
import { useLottie } from 'lottie-react';
import { motion, Easing } from 'framer-motion';

// Individual emoji component
const EmojiItem = ({ animationData, index }: { animationData: any; index: number }) => {
  const options = {
    animationData: animationData,
    loop: true,
    autoplay: true,
  };
  const { View } = useLottie(options);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ 
        duration: 0.5, 
        ease: "easeOut" as Easing,
        delay: index * 0.1 // Stagger each emoji
      }}
      style={{
        width: '80px',
        height: '80px',
        borderRadius: '12px',
        overflow: 'hidden',
        background: 'rgba(255, 255, 255, 0.5)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        border: '2px solid rgba(14, 165, 233, 0.3)'
      }}
      whileHover={{ scale: 1.1 }}
    >
      {View}
    </motion.div>
  );
};

const EmojiGallery = () => {
  const [animations, setAnimations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Load all emojis
  const emojiFiles = [
    '/Avatars/lottie.json',      // Face with monocle - attentive
    '/Avatars/lottie-2.json',    // Thinking face - hand on chin
    '/Avatars/lottie-3.json',    // Grinning face - happy
    '/Avatars/lottie-5.json',    // Sleeping face - Z's floating
    '/Avatars/lottie-7.json',    // Spiral eyes - confused/error
  ];

  useEffect(() => {
    const loadAllAnimations = async () => {
      try {
        console.log('Loading all emojis...');
        const loadedAnimations = await Promise.all(
          emojiFiles.map(async (file) => {
            const response = await fetch(file + `?t=${Date.now()}`);
            if (!response.ok) {
              throw new Error(`Failed to load ${file}: ${response.status}`);
            }
            const data = await response.json();
            return data;
          })
        );
        console.log('Successfully loaded all emojis:', loadedAnimations.length);
        setAnimations(loadedAnimations);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load animations:', error);
        setLoading(false);
      }
    };

    loadAllAnimations();
  }, []);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-soft)', fontSize: '1rem', minHeight: '60px' }}>Loading emojis...</div>;
  }

  if (animations.length === 0) {
    return <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-soft)', fontSize: '1rem', minHeight: '60px' }}>No emojis loaded</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" as Easing }}
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px',
        padding: '20px',
        flexWrap: 'wrap'
      }}
    >
      {animations.map((animationData, index) => (
        <EmojiItem key={index} animationData={animationData} index={index} />
      ))}
    </motion.div>
  );
};

export default EmojiGallery;