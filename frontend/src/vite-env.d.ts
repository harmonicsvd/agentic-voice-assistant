/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_AGENT_INTERNAL_API_KEY: string
  readonly VITE_BACKEND_AGENT_URL: string
  readonly VITE_VOICE_AGENT_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}