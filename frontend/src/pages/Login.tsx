import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Flame, Mail, Lock, User as UserIcon, Phone, ArrowRight, ShieldCheck, Eye, EyeOff } from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function Login() {
  const navigate = useNavigate()
  const { login, register } = useAuth()

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Form states
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')

  const handleToggleMode = (newMode: 'login' | 'register') => {
    setMode(newMode)
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const cleanEmail = email.trim().toLowerCase()
    const cleanPassword = password

    if (!cleanEmail || !cleanPassword) {
      setError('Please fill in all required fields.')
      return
    }

    if (mode === 'register' && !name.trim()) {
      setError('Please enter your full name.')
      return
    }

    if (mode === 'register' && cleanPassword.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setIsLoading(true)

    try {
      if (mode === 'login') {
        await login({ email: cleanEmail, password: cleanPassword })
      } else {
        await register({
          name: name.trim(),
          email: cleanEmail,
          phone: phone.trim() || undefined,
          password: cleanPassword,
        })
      }
      navigate('/')
    } catch (err: any) {
      console.error('[Authentication Error]', err)
      const detail = err?.response?.data?.detail
      if (err?.response?.status === 409) {
        setError(detail || 'An account with this email address already exists.')
      } else if (err?.response?.status === 401) {
        setError(detail || 'Invalid email address or password.')
      } else {
        setError(detail || err?.message || 'Authentication failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 px-4 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md bg-slate-800/80 border border-slate-700/80 rounded-3xl p-8 shadow-2xl backdrop-blur-xl z-10">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="h-14 w-14 rounded-2xl bg-primary flex items-center justify-center text-white shadow-xl shadow-primary/30 mb-3">
            <Flame className="h-8 w-8 fill-current" />
          </div>

          <h1 className="text-2xl font-black tracking-tight text-white">
            SafeGas AI
          </h1>

          <p className="text-xs text-slate-400 mt-1 font-medium">
            Smart LPG Safety & AI Kitchen Assistant
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 bg-slate-900/80 rounded-xl mb-6 border border-slate-700/50">
          <button
            type="button"
            onClick={() => handleToggleMode('login')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all duration-200 ${
              mode === 'login'
                ? 'bg-primary text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => handleToggleMode('register')}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all duration-200 ${
              mode === 'register'
                ? 'bg-primary text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Form Header */}
        <div className="text-center space-y-1 mb-6">
          <h2 className="text-lg font-bold text-white">
            {mode === 'login' ? 'Welcome Back' : 'Get Started with SafeGas'}
          </h2>
          <p className="text-xs text-slate-400">
            {mode === 'login'
              ? 'Enter your credentials to access safety alerts & analytics'
              : 'Register to manage cylinder safety & AI predictions'}
          </p>
        </div>

        {error && (
          <div className="mb-4 text-xs text-red-400 bg-red-950/40 border border-red-800/50 p-3 rounded-xl text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Full Name <span className="text-red-400">*</span>
              </label>
              <Input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                leftIcon={<UserIcon className="h-4 w-4" />}
                className="bg-slate-900/60 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Email Address <span className="text-red-400">*</span>
            </label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              leftIcon={<Mail className="h-4 w-4" />}
              className="bg-slate-900/60 border-slate-700 text-white placeholder:text-slate-500"
            />
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Mobile Number <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <Input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                leftIcon={<Phone className="h-4 w-4" />}
                className="bg-slate-900/60 border-slate-700 text-white placeholder:text-slate-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Password <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Minimum 8 characters' : '••••••••'}
                leftIcon={<Lock className="h-4 w-4" />}
                className="bg-slate-900/60 border-slate-700 text-white placeholder:text-slate-500 pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-11 text-sm font-bold shadow-lg shadow-primary/30 mt-2"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="h-4 w-4" />}
          >
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </Button>
        </form>

        {/* Footer Features */}
        <div className="mt-8 pt-6 border-t border-slate-700/60 flex items-center justify-around text-slate-400 text-[11px]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-primary" />
            24/7 Leak Guard
          </span>

          <span className="flex items-center gap-1.5">
            <Flame className="h-3.5 w-3.5 text-amber-500" />
            Refill Predictor
          </span>
        </div>
      </div>
    </div>
  )
}