'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { GraduationCap, ArrowLeft, Send, Loader2, AlertCircle, CheckCircle, Info, Zap, TrendingUp, Atom } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const EXAMPLE_MOLECULES = [
  { name: 'Aspirin',       smiles: 'CC(=O)Oc1ccccc1C(=O)O',          desc: 'Anti-enflamatuvar' },
  { name: '5-Fluorourasil',smiles: 'O=c1[nH]cc(F)c(=O)[nH]1',         desc: 'Anti-kanser' },
  { name: 'Ibuprofen',     smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',      desc: 'Ağrı kesici' },
  { name: 'Kafein',        smiles: 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',      desc: 'Stimülant' },
  { name: 'Imatinib',      smiles: 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C', desc: 'Lösemi ilacı' },
]

type PredictResult = {
  predicted_pKd: number | null
  confidence:    number
  runtime_ms:    number
  model_version: string
  is_mock:       boolean
  error:         string | null
  affinity_label?:string
}

function getAffinityColor(pkd: number | null) {
  if (pkd === null) return { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', label: 'Bilinmiyor', width: '0%' }
  if (pkd >= 9)     return { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  label: '⭐ Çok Güçlü', width: `${Math.min((pkd/12)*100, 100)}%` }
  if (pkd >= 7)     return { color: '#3b82f6', bg: 'rgba(59,130,246,0.12)', label: 'Güçlü (İlaç Adayı)', width: `${(pkd/12)*100}%` }
  if (pkd >= 5)     return { color: '#eab308', bg: 'rgba(234,179,8,0.12)', label: 'Orta', width: `${(pkd/12)*100}%` }
  return               { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Zayıf', width: `${(pkd/12)*100}%` }
}

function PKdMeter({ pkd }: { pkd: number | null }) {
  const meta = getAffinityColor(pkd)
  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-5xl font-black" style={{ color: meta.color }}>
            {pkd !== null ? pkd.toFixed(3) : '—'}
          </div>
          <div className="text-sm text-dark-300 mt-1">pKd Değeri</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-dark-100">{meta.label}</div>
          <div className="text-xs text-dark-400">Bağlanma gücü</div>
        </div>
      </div>
      {/* Gauge bar */}
      <div className="h-3 bg-dark-600 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: meta.width, background: `linear-gradient(90deg, ${meta.color}88, ${meta.color})` }}
        />
      </div>
      <div className="flex justify-between text-xs text-dark-400">
        <span>0 (Yok)</span>
        <span>5 (Zayıf)</span>
        <span>7 (Orta)</span>
        <span>9 (Güçlü)</span>
        <span>12+</span>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [smiles, setSmiles]     = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState<PredictResult | null>(null)
  const [error, setError]       = useState<string | null>(null)

  const predict = useCallback(async () => {
    if (!smiles.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: smiles.trim(), mode: 'fast' }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'API hatası')
        return
      }

      setResult(data)
    } catch (e) {
      setError('API bağlantısı kurulamadı. Backend çalışıyor mu? (localhost:8000)')
    } finally {
      setLoading(false)
    }
  }, [smiles])

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) predict()
  }

  return (
    <div className="min-h-screen molecule-bg" style={{ backgroundColor: '#0a0f1a' }}>
      {/* Header */}
      <header className="border-b border-white/6 px-6 py-4"
        style={{ background: 'rgba(10,15,26,0.9)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
                <GraduationCap className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white">NeoBioAI</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-400">Dashboard</span>
            </div>
          </div>
          <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer"
            className="btn-ghost text-xs px-4 py-2">
            API Docs
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Sol: Giriş */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-black text-dark-100 mb-2">Binding Affinity Tahmini</h1>
              <p className="text-dark-300">SMILES girin → GNN modeli ile pKd değeri alın.</p>
            </div>

            {/* SMILES Input */}
            <div className="card">
              <label className="block text-sm font-semibold text-dark-200 mb-3">
                SMILES Dizisi
                <span className="ml-2 text-dark-400 font-normal text-xs">Ctrl+Enter ile gönder</span>
              </label>
              <textarea
                id="smiles-input"
                className="input-field resize-none"
                rows={3}
                placeholder="Örnek: CC(=O)Oc1ccccc1C(=O)O"
                value={smiles}
                onChange={(e) => setSmiles(e.target.value)}
                onKeyDown={handleKey}
              />
              <button
                id="predict-button"
                onClick={predict}
                disabled={loading || !smiles.trim()}
                className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Tahmin ediliyor...</>
                ) : (
                  <><Send className="w-4 h-4" /> Tahmin Et</>
                )}
              </button>
            </div>

            {/* Örnek Moleküller */}
            <div className="card">
              <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-400" /> Hazır Örnekler
              </h3>
              <div className="space-y-2">
                {EXAMPLE_MOLECULES.map((mol) => (
                  <button
                    key={mol.name}
                    id={`example-${mol.name.toLowerCase().replace(/[^a-z]/g, '-')}`}
                    onClick={() => setSmiles(mol.smiles)}
                    className="w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 group"
                    style={{ border: '1px solid rgba(255,255,255,0.06)' }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)'
                      e.currentTarget.style.background  = 'rgba(59,130,246,0.05)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
                      e.currentTarget.style.background  = 'transparent'
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-dark-200 group-hover:text-blue-400 transition-colors">{mol.name}</span>
                      <span className="text-xs text-dark-400">{mol.desc}</span>
                    </div>
                    <p className="font-mono text-xs text-dark-400 truncate">{mol.smiles}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* pKd Açıklaması */}
            <div className="card flex gap-3 items-start">
              <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-dark-200 mb-1">pKd Nedir?</h4>
                <p className="text-xs text-dark-300 leading-relaxed">
                  pKd = −log₁₀(Kd) — bağlanma sabitinin negatif logaritması.
                  Yüksek pKd daha güçlü bağlanma anlamına gelir.
                  İlaç adayları genellikle pKd ≥ 7 (Kd ≤ 100 nM) gerektirir.
                </p>
              </div>
            </div>
          </div>

          {/* Sağ: Sonuçlar */}
          <div className="space-y-6">
            {!result && !error && !loading && (
              <div className="card h-64 flex flex-col items-center justify-center text-center">
                <GraduationCap className="w-16 h-16 text-slate-600 mb-4 animate-float" />
                <p className="text-dark-400 font-medium">Sonuç burada görünecek</p>
                <p className="text-dark-500 text-sm mt-1">SMILES girin ve &quot;Tahmin Et&quot; butonuna tıklayın</p>
              </div>
            )}

            {loading && (
              <div className="card h-64 flex flex-col items-center justify-center text-center">
                <div className="relative mb-6">
                  <Atom className="w-16 h-16 text-blue-500 animate-spin" style={{ animationDuration: '3s' }} />
                  <div className="absolute inset-0 rounded-full animate-ping"
                    style={{ background: 'rgba(59,130,246,0.1)', animationDuration: '2s' }} />
                </div>
                <p className="text-dark-300 font-medium">GNN çalışıyor...</p>
                <p className="text-dark-400 text-sm mt-1">Graf oluşturuluyor, inference yapılıyor</p>
              </div>
            )}

            {error && (
              <div className="card border border-red-500/20" style={{ background: 'rgba(244,112,103,0.05)' }}>
                <div className="flex gap-3 items-start">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-red-400 mb-1">Hata</h3>
                    <p className="text-sm text-dark-300">{error}</p>
                    <p className="text-xs text-dark-400 mt-2">
                      Backend başlatmak için: <code className="font-mono bg-dark-700 px-1 rounded">cd neodock &amp;&amp; python -m uvicorn backend.main:app --reload</code>
                    </p>
                  </div>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-4 animate-fade-in">
                {/* Ana sonuç */}
                <div className="card" style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.2)' }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-blue-400" />
                      <span className="font-semibold text-dark-200">Tahmin Tamamlandı</span>
                    </div>
                    {result.is_mock && (
                      <span className="badge-yellow">Mock Mod</span>
                    )}
                  </div>
                  <PKdMeter pkd={result.predicted_pKd} />
                </div>

                {/* Meta bilgiler */}
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: 'Süre',    value: `${result.runtime_ms.toFixed(1)}ms`, icon: Zap },
                    { label: 'Model',   value: result.model_version,                icon: Atom },
                    { label: 'Güven',   value: result.confidence > 0 ? `${(result.confidence*100).toFixed(0)}%` : 'N/A', icon: TrendingUp },
                  ].map(({ label, value, icon: Icon }) => (
                    <div key={label} className="card text-center">
                      <Icon className="w-4 h-4 text-dark-400 mx-auto mb-1.5" />
                      <div className="font-mono font-bold text-dark-100 text-sm">{value}</div>
                      <div className="text-xs text-dark-400 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>

                {/* SMILES */}
                <div className="card">
                  <div className="text-xs text-dark-400 mb-1.5 font-semibold uppercase tracking-wide">Analiz Edilen SMILES</div>
                  <p className="font-mono text-xs text-dark-300 break-all leading-relaxed">{smiles}</p>
                </div>

                {/* Mock uyarı */}
                {result.is_mock && (
                  <div className="card flex gap-3 items-start" style={{ borderColor: 'rgba(227,179,65,0.2)' }}>
                    <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-dark-300">
                      <strong className="text-amber-400">Mock Mod:</strong> GNN model ağırlıkları yüklenmemiş.
                      Değerler SMILES hash&apos;inden deterministik üretildi.
                      Gerçek tahmin için modeli eğitin: <code className="font-mono bg-dark-700 px-1 rounded">python ml/train.py</code>
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
