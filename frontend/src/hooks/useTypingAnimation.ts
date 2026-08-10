import { useState, useEffect } from 'react';

interface UseTypingAnimationProps {
  firstPhrase: string;
  finalPhrase: string;
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseBeforeDelete?: number;
  pauseAfterDelete?: number;
}

export const useTypingAnimation = ({
  firstPhrase,
  finalPhrase,
  typingSpeed = 50,
  deletingSpeed = 30,
  pauseBeforeDelete = 1500,
  pauseAfterDelete = 300
}: UseTypingAnimationProps) => {
  const [text, setText] = useState('');
  const [phase, setPhase] = useState(0); // 0: typing first, 1: deleting, 2: typing second
  const [animationComplete, setAnimationComplete] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (phase === 0) {
        // Typing first phrase character by character
        if (text.length < firstPhrase.length) {
          setText(firstPhrase.substring(0, text.length + 1));
        } else {
          // Finished typing, pause then start deleting
          setTimeout(() => setPhase(1), pauseBeforeDelete);
        }
      } else if (phase === 1) {
        // Deleting only "assistant" part character by character
        if (text.length > 'Your personal '.length) {
          setText(text.substring(0, text.length - 1));
        } else {
          // Finished deleting, pause then type second part
          setTimeout(() => setPhase(2), pauseAfterDelete);
        }
      } else if (phase === 2) {
        // Typing second part character by character
        if (text.length < finalPhrase.length) {
          setText(finalPhrase.substring(0, text.length + 1));
        } else {
          // Animation complete
          setAnimationComplete(true);
        }
      }
    }, phase === 1 ? deletingSpeed : typingSpeed);

    return () => clearTimeout(timer);
  }, [text, phase, firstPhrase, finalPhrase, typingSpeed, deletingSpeed, pauseBeforeDelete, pauseAfterDelete]);

  return { text, animationComplete };
};