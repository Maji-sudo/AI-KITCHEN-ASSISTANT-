import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { AuthProvider, setQueryCacheResetter } from '@/contexts/AuthContext'
import { AppRoutes } from '@/routes'

// Single shared QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

// Wire up the cache-reset function so AuthContext can call it on logout
// without needing a direct import of queryClient.
function QueryCacheResetWirer() {
  useEffect(() => {
    setQueryCacheResetter(() => {
      queryClient.clear()
    })
  }, [])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <QueryCacheResetWirer />
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
