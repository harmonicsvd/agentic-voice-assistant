/**
 * UI Configuration - Centralized UI strings and settings
 * This makes the frontend more maintainable and easier to localize
 */

// Character state type definition
export type CharacterState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'processing' | 'success' | 'error';

export const UI_CONFIG = {
  voiceSession: {
    buttonLabels: {
      startCall: 'Tap to start call',
      endCall: 'Tap to end call',
    },
    buttonHints: {
      idle: 'Speak naturally — the agent will guide you',
      listening: 'Listening...',
      disconnected: 'Speak naturally',
    },
    statusMessages: {
      connecting: 'Connecting...',
      listening: 'Listening...',
      disconnected: 'Disconnected',
      failed: 'Failed',
      clientNotAvailable: 'Client not available',
    },
    characterStates: {
      idle: 'idle' as CharacterState,
      listening: 'listening' as CharacterState, 
      thinking: 'thinking' as CharacterState,
      speaking: 'speaking' as CharacterState,
      processing: 'processing' as CharacterState,
      success: 'success' as CharacterState,
      error: 'error' as CharacterState,
    }
  },
  pages: {
    login: {
      title: 'Voice Assistant',
      subtitle: 'Sign in to access your voice scheduling assistant',
    },
    setup: {
      title: 'Setup Profile',
      subtitle: 'Configure your preferences for better assistance',
    },
    profile: {
      title: 'Your Profile',
      subtitle: 'Manage your personal settings',
    },
    documents: {
      title: 'Documents',
      subtitle: 'Upload and manage your knowledge base',
    }
  },
  colors: {
    primary: '#0ea5e9',
    secondary: '#64748B',
    success: '#10b981',
    error: '#ef4444',
    background: '#F7F9FC',
  },
  animation: {
    pulseDuration: '2s',
    pulseDelay: '0.3s',
  }
};