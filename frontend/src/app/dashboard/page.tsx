'use client'

import { useState, useCallback, useEffect } from 'react'
import Link from 'next/link'
import {
  GraduationCap, ArrowLeft, Send, Loader2, AlertCircle, CheckCircle, Info,
  Zap, TrendingUp, Atom, Sparkles, FileText, Table, Box,
} from 'lucide-react'

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

type TopAtom = { atom_idx: number; symbol: string; contribution: number; direction: string }
type ExplainResult = { method: string; n_atoms: number; atoms: string[]; contribs: number[]; top_atoms: TopAtom[]; is_mock: boolean }
type ReportResult  = { report: string; report_backend: string; report_model: string }

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
      <div className="h-3 bg-dark-600 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: meta.width, background: `linear-gradient(90deg, ${meta.color}88, ${meta.color})` }}
        />
      </div>
      <div className="flex justify-between text-xs text-dark-400">
        <span>0 (Yok)</span><span>5 (Zayıf)</span><span>7 (Orta)</span><span>9 (Güçlü)</span><span>12+</span>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [smiles, setSmiles]     = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState<PredictResult | null>(null)
  const [error, setError]       = useState<string | null>(null)
  const [explainData, setExplainData] = useState<ExplainResult | null>(null)
  const [explainLoading, setExplainLoading] = useState(false)
  const [report, setReport]     = useState<ReportResult | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  const predict = useCallback(async () => {
    if (!smiles.trim()) return
    setLoading(true); setError(null); setResult(null); setExplainData(null); setReport(null)
    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: smiles.trim(), mode: 'fast' }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'API hatası'); return }
      setResult(data)
    } catch (e) {
      setError('API bağlantısı kurulamadı. Backend çalışıyor mu? (localhost:8000)')
    } finally { setLoading(false) }
  }, [smiles])

  const runExplain = useCallback(async () => {
    if (!smiles.trim()) return
    setExplainLoading(true); setExplainData(null)
    try {
      const res = await fetch(`${API_URL}/explain`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: smiles.trim(), steps: 20, top_k: 10 }),
      })
      const data = await res.json()
      if (res.ok) setExplainData(data)
    } catch {} finally { setExplainLoading(false) }
  }, [smiles])

  const runReport = useCallback(async () => {
    if (!smiles.trim()) return
    setReportLoading(true); setReport(null)
    try {
      const res = await fetch(`${API_URL}/report`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: smiles.trim(), explain: true, force_local: true }),
      })
      const data = await res.json()
      if (res.ok) setReport({ report: data.report, report_backend: data.report_backend, report_model: data.report_model })
    } catch {} finally { setReportLoading(false) }
  }, [smiles])

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) predict()
  }

  return (
    <div className="min-h-screen molecule-bg" style={{ backgroundColor: '#0a0f1a' }}>
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
          <div className="flex items-center gap-2">
            <Link href="/model"  className="btn-ghost text-xs px-3 py-2 flex items-center gap-1"><Atom className="w-3 h-3"/>Model</Link>
            <Link href="/batch"  className="btn-ghost text-xs px-3 py-2 flex items-center gap-1"><Table className="w-3 h-3"/>Batch CSV</Link>
            <Link href="/viewer" className="btn-ghost text-xs px-3 py-2 flex items-center gap-1"><Box className="w-3 h-3"/>3D Viewer</Link>
            <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer"
              className="btn-ghost text-xs px-3 py-2">API Docs</a>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Sol */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-black text-dark-100 mb-2">Binding Affinity Tahmini</h1>
              <p className="text-dark-300">SMILES girin → GNN + Integrated Gradients + LLM rapor.</p>
            </div>

            <div className="card">
              <label className="block text-sm font-semibold text-dark-200 mb-3">
                SMILES Dizisi
                <span className="ml-2 text-dark-400 font-normal text-xs">Ctrl+Enter ile gönder</span>
              </label>
              <textarea id="smiles-input" className="input-field resize-none" rows={3}
                placeholder="Örnek: CC(=O)Oc1ccccc1C(=O)O" value={smiles}
                onChange={(e) => setSmiles(e.target.value)} onKeyDown={handleKey} />
              <button id="predict-button" onClick={predict} disabled={loading || !smiles.trim()}
                className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
                {loading ? (<><Loader2 className="w-4 h-4 animate-spin" /> Tahmin ediliyor...</>)
                         : (<><Send className="w-4 h-4" /> Tahmin Et</>)}
              </button>
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-dark-200 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-blue-400" /> Hazır Örnekler
              </h3>
              <div className="space-y-2">
                {EXAMPLE_MOLECULES.map((mol) => (
                  <button key={mol.name} onClick={() => setSmiles(mol.smiles)}
                    className="w-full text-left px-3 py-2.5 rounded-lg transition-all"
                    style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-dark-200">{mol.name}</span>
                      <span className="text-xs text-dark-400">{mol.desc}</span>
                    </div>
                    <p className="font-mono text-xs text-dark-400 truncate">{mol.smiles}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="card flex gap-3 items-start">
              <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-dark-200 mb-1">pKd Nedir?</h4>
                <p className="text-xs text-dark-300 leading-relaxed">
                  pKd = −log₁₀(Kd). Yüksek pKd daha güçlü bağlanma anlamına gelir.
                  İlaç adayları genellikle pKd ≥ 7 (Kd ≤ 100 nM) gerektirir.
                </p>
              </div>
            </div>
          </div>

          {/* Sağ */}
          <div className="space-y-6">
            {!result && !error && !loading && (
              <div className="card h-64 flex flex-col items-center justify-center text-center">
                <GraduationCap className="w-16 h-16 text-slate-600 mb-4 animate-float" />
                <p className="text-dark-400 font-medium">Sonuç burada görünecek</p>
                <p className="text-dark-500 text-sm mt-1">SMILES girin ve &quot;Tahmin Et&quot;</p>
              </div>
            )}

            {loading && (
              <div className="card h-64 flex flex-col items-center justify-center text-center">
                <Atom className="w-16 h-16 text-blue-500 animate-spin mb-6" style={{ animationDuration: '3s' }} />
                <p className="text-dark-300 font-medium">GNN çalışıyor...</p>
              </div>
            )}

            {error && (
              <div className="card border border-red-500/20" style={{ background: 'rgba(244,112,103,0.05)' }}>
                <div className="flex gap-3 items-start">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-red-400 mb-1">Hata</h3>
                    <p className="text-sm text-dark-300">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-4 animate-fade-in">
                <div className="card" style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.2)' }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-blue-400" />
                      <span className="font-semibold text-dark-200">Tahmin Tamamlandı</span>
                    </div>
                    {result.is_mock && (<span className="badge-yellow">Mock Mod</span>)}
                  </div>
                  <PKdMeter pkd={result.predicted_pKd} />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: 'Süre',  value: `${result.runtime_ms.toFixed(1)}ms`, icon: Zap },
                    { label: 'Model', value: result.model_version,                icon: Atom },
                    { label: 'Güven', value: result.confidence > 0 ? `${(result.confidence*100).toFixed(0)}%` : 'N/A', icon: TrendingUp },
                  ].map(({ label, value, icon: Icon }) => (
                    <div key={label} className="card text-center">
                      <Icon className="w-4 h-4 text-dark-400 mx-auto mb-1.5" />
                      <div className="font-mono font-bold text-dark-100 text-sm">{value}</div>
                      <div className="text-xs text-dark-400 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>

                {/* Explain & Rapor butonlari */}
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={runExplain} disabled={explainLoading}
                    className="btn-ghost flex items-center justify-center gap-2 py-3"
                    style={{ border: '1px solid rgba(168,85,247,0.3)', color: '#c084fc' }}>
                    {explainLoading
                      ? <><Loader2 className="w-4 h-4 animate-spin" /> Analiz...</>
                      : <><Sparkles className="w-4 h-4" /> Explain (Atomlar)</>}
                  </button>
                  <button onClick={runReport} disabled={reportLoading}
                    className="btn-ghost flex items-center justify-center gap-2 py-3"
                    style={{ border: '1px solid rgba(34,197,94,0.3)', color: '#4ade80' }}>
                    {reportLoading
                      ? <><Loader2 className="w-4 h-4 animate-spin" /> Rapor...</>
                      : <><FileText className="w-4 h-4" /> AI Rapor Üret</>}
                  </button>
                </div>

                {/* Explainability paneli */}
                {explainData && (
                  <div className="card animate-fade-in" style={{ border: '1px solid rgba(168,85,247,0.2)', background: 'rgba(168,85,247,0.04)' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      <span className="font-semibold text-dark-200">Atom Katki Analizi</span>
                      <span className="badge" style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc', padding: '2px 8px', borderRadius: '4px', fontSize: '10px' }}>
                        {explainData.method}
                      </span>
                    </div>
                    <p className="text-xs text-dark-400 mb-3">
                      En etkili {explainData.top_atoms.length} atom ({explainData.n_atoms} toplam):
                    </p>
                    <div className="space-y-1.5">
                      {explainData.top_atoms.map((a, i) => {
                        const max = Math.max(...explainData.top_atoms.map(x => Math.abs(x.contribution)))
                        const pct = (Math.abs(a.contribution) / max) * 100
                        const isPos = a.contribution > 0
                        return (
                          <div key={i} className="flex items-center gap-2 text-xs">
                            <span className="font-mono text-dark-300 w-16">[{a.atom_idx}] {a.symbol}</span>
                            <div className="flex-1 h-2 bg-dark-700 rounded overflow-hidden">
                              <div className="h-full rounded" style={{
                                width: `${pct}%`,
                                background: isPos ? '#22c55e' : '#ef4444',
                              }} />
                            </div>
                            <span className="font-mono text-dark-300 w-20 text-right">
                              {a.contribution > 0 ? '+' : ''}{a.contribution.toFixed(3)}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                    <p className="text-xs text-dark-500 mt-3">
                      🟢 pKd&apos;yi artıran atomlar · 🔴 azaltan atomlar
                    </p>
                  </div>
                )}

                {/* LLM Rapor paneli */}
                {report && (
                  <div className="card animate-fade-in" style={{ border: '1px solid rgba(34,197,94,0.2)', background: 'rgba(34,197,94,0.04)' }}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-green-400" />
                        <span className="font-semibold text-dark-200">AI Rapor</span>
                      </div>
                      <span className="text-xs text-dark-400">{report.report_backend} / {report.report_model}</span>
                    </div>
                    <div className="text-sm text-dark-200 leading-relaxed whitespace-pre-wrap">{report.report}</div>
                  </div>
                )}

                <div className="card">
                  <div className="text-xs text-dark-400 mb-1.5 font-semibold uppercase tracking-wide">Analiz Edilen SMILES</div>
                  <p className="font-mono text-xs text-dark-300 break-all leading-relaxed">{smiles}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
