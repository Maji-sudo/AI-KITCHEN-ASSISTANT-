import axios from 'axios'

/**
 * Resolves the API base URL from Vite environment variables.
 * Supports both VITE_API_BASE_URL (recommended) and VITE_API_URL (backward-compatible).
 * Guarantees a normalized URL ending in '/api/v1' without duplicate slashes.
 */
export function resolveApiBase(
  baseUrlEnv?: string,
  urlEnv?: string,
  isProd = import.meta.env.PROD
): string {
  const configured = (baseUrlEnv || urlEnv || '').trim()

  if (!configured) {
    if (isProd && typeof window !== 'undefined') {
      console.warn(
        '[SafeGas AI] Neither VITE_API_BASE_URL nor VITE_API_URL is configured in production. ' +
        'API calls will fall back to /api/v1 on the current origin. ' +
        'Set VITE_API_BASE_URL in your Vercel project settings and redeploy.'
      )
    }
    return '/api/v1'
  }

  const clean = configured.replace(/\/+$/, '')
  return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`
}

export const API_BASE = resolveApiBase(
  import.meta.env.VITE_API_BASE_URL,
  import.meta.env.VITE_API_URL
)

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Attach JWT token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_name')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_phone')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
