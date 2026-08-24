import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Flame,
  Phone,
  KeyRound,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react'

import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [step, setStep] = useState<'phone' | 'otp'>('phone')
  const [phone, setPhone] = useState('+91 98765 43210')
  const [otp, setOtp] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // ==========================================================
  // GET VERIFICATION CODE
  // ==========================================================
  // Development mode:
  // We don't actually send an SMS.
  // We directly move to the OTP screen.
  //
  // Testing OTP: 123456
  // ==========================================================

  const handleSendOtp = (e: React.FormEvent) => {
    e.preventDefault()

    if (!phone || phone.length < 10) {
      setError('Please enter a valid phone number')
      return
    }

    setError('')
    setStep('otp')
  }

  // ==========================================================
  // VERIFY OTP
  // ==========================================================

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()

    if (otp.length !== 6) {
      setError('Please enter the 6-digit OTP code')
      return
    }

    setError('')
    setIsLoading(true)

    try {
      // Existing authentication flow
      // Backend will accept 123456 in DEBUG mode
      await login(phone, otp)

      // Go to dashboard
      navigate('/')
    } catch {
      setError('Invalid OTP code. Try entering 123456 (demo code).')
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

        {/* Brand */}
        <div className="flex flex-col items-center text-center mb-8">

          <div className="h-14 w-14 rounded-2xl bg-primary flex items-center justify-center text-white shadow-xl shadow-primary/30 mb-3">
            <Flame className="h-8 w-8 fill-current" />
          </div>

          <h1 className="text-2xl font-black tracking-tight">
            SafeGas AI
          </h1>

          <p className="text-xs text-slate-400 mt-1 font-medium">
            Smart LPG Safety & AI Kitchen Assistant
          </p>

        </div>

        {/* ======================================================
            PHONE STEP
            ====================================================== */}

        {step === 'phone' ? (

          <form
            onSubmit={handleSendOtp}
            className="space-y-4"
          >

            <div>

              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Mobile Number
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

            {error && (
              <p className="text-xs text-danger text-center">
                {error}
              </p>
            )}

            <Button
              type="submit"
              className="w-full h-11 text-sm font-bold shadow-lg shadow-primary/30"
              isLoading={isLoading}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Get Verification Code
            </Button>

          </form>

        ) : (

          /* ====================================================
             OTP STEP
             ==================================================== */

          <form
            onSubmit={handleVerifyOtp}
            className="space-y-4"
          >

            {/* Demo OTP message */}

            <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 flex items-center gap-3 text-xs text-primary mb-2">

              <CheckCircle2 className="h-5 w-5 shrink-0" />

              <span>
                Verification code sent to{' '}
                <strong>{phone}</strong>
                {' '}
                (Demo OTP:{' '}
                <strong>123456</strong>
                )
              </span>

            </div>

            {/* OTP Input */}

            <div>

              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Enter 6-Digit OTP
              </label>

              <Input
                type="text"
                maxLength={6}
                value={otp}
                onChange={(e) => {
                  // Only allow numbers
                  const value = e.target.value.replace(/\D/g, '')
                  setOtp(value)
                }}
                placeholder="123456"
                leftIcon={<KeyRound className="h-4 w-4" />}
                className="bg-slate-900/60 border-slate-700 text-white tracking-widest text-center text-lg font-bold"
              />

            </div>

            {/* Error */}

            {error && (
              <p className="text-xs text-danger text-center">
                {error}
              </p>
            )}

            {/* Verify Button */}

            <Button
              type="submit"
              className="w-full h-11 text-sm font-bold shadow-lg shadow-primary/30"
              isLoading={isLoading}
            >
              Verify & Sign In
            </Button>

            {/* Change Number */}

            <button
              type="button"
              onClick={() => {
                setStep('phone')
                setOtp('')
                setError('')
              }}
              className="w-full text-xs text-slate-400 hover:text-white transition-colors text-center"
            >
              Change Mobile Number
            </button>

          </form>

        )}

        {/* ======================================================
            FOOTER FEATURES
            ====================================================== */}

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