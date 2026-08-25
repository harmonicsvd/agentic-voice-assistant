import { useState, useEffect } from 'react';
import { Joyride, Step } from 'react-joyride';

const TOUR_STEPS: Step[] = [
  {
    target: '.skills-button',
    content: 'Click here to install and manage your skills.',
  },
  {
    target: '.wake-word-status',
    content: 'This shows if the voice agent is awake or sleeping. Say "are you there?" to wake her up',
  },
  {
    target: '.voice-assistant-container',
    content: 'This is your voice assistant EMO. Speak naturally to interact.',
  },
  {
    target: '.profile-button',
    content: 'Click here to view and edit your profile settings.',
  },
  {
    target: '.tour-button',
    content: 'Click this Tour button anytime to replay this guide.',
  },
];

interface TourGuideProps {
  run?: boolean;
  onTourComplete?: () => void;
}

export const TourGuide = ({ run = false, onTourComplete }: TourGuideProps) => {
  const [tourRun, setTourRun] = useState(run);

  useEffect(() => {
    console.log('TourGuide run prop changed:', run);
    setTourRun(run);
  }, [run]);

  const handleTourEvent = (data: any) => {
    const { status, action, type } = data;
    console.log('Tour event:', { status, action, type });
    if (status === 'finished' || status === 'skipped' || action === 'skip') {
      localStorage.setItem('tourCompleted', 'true');
      console.log('Tour marked as completed');
      if (onTourComplete) {
        onTourComplete();
      }
    }
  };

  return (
    <div style={{ position: 'relative', zIndex: 99999 }}>
      <Joyride
        steps={TOUR_STEPS}
        run={tourRun}
        continuous
        options={{ buttons: ['back', 'skip', 'close', 'primary'] }}
        onEvent={handleTourEvent}
        styles={{
          tooltip: {
            zIndex: 99999,
          },
          beacon: {
            zIndex: 99999,
          },
        }}
      />
    </div>
  );
};

export const hasTourCompleted = (): boolean => {
  return localStorage.getItem('tourCompleted') === 'true';
};

export const resetTour = () => {
  localStorage.removeItem('tourCompleted');
};
