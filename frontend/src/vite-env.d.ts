/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_API_URL?: string
  readonly VITE_HP_GAS_REFILL_NUMBER?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
