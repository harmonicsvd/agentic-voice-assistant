/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_WEATHER_AGENT_INTERNAL_API_KEY: string
  readonly VITE_WEATHER_AGENT_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}