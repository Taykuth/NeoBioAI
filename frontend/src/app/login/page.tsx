'use client'

import { useState } from 'react'
import Link from 'next/link'
import { GraduationCap, ArrowLeft, Eye, EyeOff, Loader2, LogIn } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function LoginPage() {
  const [email, setEmail]       = useState('demo@neodock.dev')
  const [password, setPassword] = useState('demo1234')
  const [showPw, setShowPw]     = useState(false)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [token, setToken]       = useState<string | null>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Giriş başarısız'); return }
      localStorage.setItem('neodock_token', data.access_token)
      setToken(data.access_token)
    } catch {
      setError('API bağlantısı kurulamadı')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 molecule-bg flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-3 mb-8">
          <Link href="/" className="text-dark-400 hover:text-dark-200 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-dark-100">NeoBioAI</span>
          </div>
        </div>

        <div className="card glow-border">
          <h1 className="text-2xl font-black text-dark-100 mb-1">Giriş Yap</h1>
          <p className="text-sm text-dark-400 mb-6">JWT korumalı API erişimi için</p>

          {token ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-blue-400">
                <LogIn className="w-5 h-5" />
                <span className="font-semibold">Giriş başarılı!</span>
              </div>
              <div>
                <div className="text-xs text-dark-400 mb-1 font-semibold">Access Token</div>
                <div className="font-mono text-xs bg-dark-800 p-3 rounded-lg text-dark-300 break-all">{token}</div>
              </div>
              <Link href="/dashboard" className="btn-primary w-full flex items-center justify-center gap-2">
                Dashboard&apos;a Git <LogIn className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5" htmlFor="email-input">E-posta</label>
                <input id="email-input" type="email" className="input-field" value={email}
                  onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5" htmlFor="password-input">Şifre</label>
                <div className="relative">
                  <input id="password-input" type={showPw ? 'text' : 'password'} className="input-field pr-10"
                    value={password} onChange={(e) => setPassword(e.target.value)} required />
                  <button type="button" onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200">
                    {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              <button id="login-submit" type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
                {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Giriş yapılıyor...</> : <><LogIn className="w-4 h-4" /> Giriş Yap</>}
              </button>

              <p className="text-xs text-center text-dark-400">
                Demo: <code className="font-mono bg-dark-700 px-1 rounded">demo@neodock.dev</code> / <code className="font-mono bg-dark-700 px-1 rounded">demo1234</code>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
