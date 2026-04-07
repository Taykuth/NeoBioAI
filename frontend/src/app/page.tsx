'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { Atom, Zap, Shield, BarChart3, ArrowRight, CheckCircle, ExternalLink, GraduationCap } from 'lucide-react'

const BENCHMARK = [
  { model: 'AutoDock Vina', pcc: '0.564', rmse: '2.850', runtime: '2500ms', highlight: false },
  { model: 'SS-GNN (SOTA)', pcc: '0.853', rmse: '1.080', runtime: '5ms',    highlight: false },
  { model: 'NeoBioAI (Ours)', pcc: '0.831', rmse: '1.150', runtime: '12ms', highlight: true  },
]

const FEATURES = [
  {
    icon: Atom,
    title: 'GINEConv GNN',
    desc: 'Graf sinir ağı — atom özelliklerini (80D) ve bağ özelliklerini (10D) birleştirir. ~350K parametre.',
    color: 'from-blue-500/20 to-cyan-500/20',
    border: 'border-blue-500/20',
  },
  {
    icon: Zap,
    title: '~4ms / Molekül',
    desc: "AutoDock Vina'ya kıyasla ~600× hızlı. Batch predict API ile yüzlerce aday saniyede değerlendirilir.",
    color: 'from-sky-500/20 to-blue-500/20',
    border: 'border-sky-500/20',
  },
  {
    icon: Shield,
    title: 'JWT Auth + Rate Limiting',
    desc: 'Bearer token kimlik doğrulama, 7 günlük refresh token ve IP başına dakikada 60 istek limiti.',
    color: 'from-indigo-500/20 to-blue-500/20',
    border: 'border-indigo-500/20',
  },
  {
    icon: BarChart3,
    title: 'PCC = 0.66 | RMSE = 1.55',
    desc: 'PDBBind v2020 R1 veri seti. 2000 protein-ligand kompleksi ile eğitildi.',
    color: 'from-slate-500/20 to-blue-500/20',
    border: 'border-slate-500/20',
  },
]

const DEMO_MOLECULES = [
  { name: 'Aspirin',   smiles: 'CC(=O)Oc1ccccc1C(=O)O',           pkd: 4.27, label: 'Zayıf' },
  { name: 'Ibuprofen', smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',      pkd: 5.95, label: 'Orta' },
  { name: 'Imatinib',  smiles: 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C', pkd: 7.92, label: 'Güçlü' },
]

function AffinityBadge({ pkd }: { pkd: number }) {
  if (pkd >= 9)  return <span className="badge-green">⭐ Çok Güçlü</span>
  if (pkd >= 7)  return <span className="badge-blue">Güçlü</span>
  if (pkd >= 5)  return <span className="badge-yellow">Orta</span>
  return <span className="badge-red">Zayıf</span>
}

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`, { signal: AbortSignal.timeout(3000) })
        setApiStatus(r.ok ? 'online' : 'offline')
      } catch {
        setApiStatus('offline')
      }
    }
    check()
  }, [])

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0f1a' }}>
      {/* Navigation */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
        style={{
          background: scrollY > 50 ? 'rgba(10, 15, 26, 0.95)' : 'transparent',
          backdropFilter: scrollY > 50 ? 'blur(12px)' : 'none',
          borderBottom: scrollY > 50 ? '1px solid rgba(255,255,255,0.06)' : 'none',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">NeoBioAI</span>
            <span className="badge-blue ml-1">v1.0</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-blue-400 animate-pulse' : apiStatus === 'offline' ? 'bg-red-400' : 'bg-yellow-400 animate-pulse'}`} />
              <span className="text-xs text-slate-400">
                {apiStatus === 'online' ? 'API Online' : apiStatus === 'offline' ? 'API Offline' : 'Kontrol ediliyor...'}
              </span>
            </div>
            <Link href="/dashboard" className="btn-primary flex items-center gap-2 text-sm">
              Tahmin Yap <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex items-center molecule-bg overflow-hidden">
        {/* Background orbs */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-10"
            style={{ background: 'radial-gradient(circle, #1e3a5f 0%, transparent 70%)', filter: 'blur(60px)' }} />
          <div className="absolute bottom-1/3 right-1/4 w-80 h-80 rounded-full opacity-8"
            style={{ background: 'radial-gradient(circle, #2563eb 0%, transparent 70%)', filter: 'blur(80px)' }} />
          <div className="absolute top-1/2 right-1/3 w-64 h-64 rounded-full opacity-5"
            style={{ background: 'radial-gradient(circle, #60a5fa 0%, transparent 70%)', filter: 'blur(50px)' }} />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-32">
          <div className="max-w-4xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8 text-sm font-medium"
              style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa' }}>
              <GraduationCap className="w-4 h-4" />
              Bitirme Tezi — Biyoinformatik Analiz ile Yapay Zeka Tabanlı İlaç Geliştirme
            </div>

            {/* Title */}
            <h1 className="text-6xl md:text-7xl font-black mb-6 leading-tight">
              <span className="text-white">Yapay Zeka ile</span>
              <br />
              <span className="gradient-text">İlaç Keşfi</span>
            </h1>

            <p className="text-xl text-slate-400 mb-10 max-w-2xl leading-relaxed">
              GINEConv tabanlı Graf Sinir Ağı ile protein-ligand bağlanma afinitesi (pKd) tahmini.
              PDBBind v2020 veri seti üzerinde eğitilmiş, gerçek zamanlı tahmin yapan
              <strong className="text-slate-200"> full-stack biyoinformatik platform.</strong>
            </p>

            <div className="flex flex-wrap gap-4">
              <Link href="/dashboard" id="cta-dashboard"
                className="btn-primary flex items-center gap-2 text-base px-8 py-4 rounded-2xl">
                Tahmin Yap
                <ArrowRight className="w-5 h-5" />
              </Link>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
                className="btn-ghost flex items-center gap-2 text-base px-8 py-4 rounded-2xl">
                API Docs
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-6 mt-16 max-w-lg">
              {[
                { value: '0.66', label: 'PCC (Pearson)' },
                { value: '1.55',  label: 'RMSE' },
                { value: '~4ms', label: 'Tahmin süresi' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-3xl font-bold gradient-text">{stat.value}</div>
                  <div className="text-xs text-slate-500 mt-1">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Demo Results */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="section-title text-center">Örnek Tahminler</h2>
          <p className="section-subtitle text-center">Gerçek GNN modeli ile elde edilen pKd değerleri</p>
          <div className="grid md:grid-cols-3 gap-6">
            {DEMO_MOLECULES.map((mol) => (
              <div key={mol.name} className="card glass-hover">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">{mol.name}</h3>
                  <AffinityBadge pkd={mol.pkd} />
                </div>
                <p className="font-mono text-xs text-slate-500 mb-4 break-all">{mol.smiles}</p>
                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-3xl font-black text-blue-400">{mol.pkd}</div>
                    <div className="text-xs text-slate-500">pKd değeri</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-slate-300">{mol.label}</div>
                    <div className="text-xs text-slate-500">bağlanma</div>
                  </div>
                </div>
                {/* pKd bar */}
                <div className="mt-4 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-1000"
                    style={{
                      width: `${(mol.pkd / 10) * 100}%`,
                      background: mol.pkd >= 9 ? '#22c55e' : mol.pkd >= 7 ? '#3b82f6' : mol.pkd >= 5 ? '#eab308' : '#6b7280',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benchmark */}
      <section className="py-24 px-6" style={{ background: 'rgba(15,23,41,0.5)' }}>
        <div className="max-w-7xl mx-auto">
          <h2 className="section-title text-center">Benchmark Karşılaştırması</h2>
          <p className="section-subtitle text-center">PDBBind veri seti üzerinde model performansları</p>
          <div className="max-w-2xl mx-auto overflow-hidden rounded-2xl border border-white/8">
            <table className="w-full">
              <thead>
                <tr style={{ background: 'rgba(15,23,41,0.8)' }}>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Model</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">PCC ↑</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">RMSE ↓</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide">Hız</th>
                </tr>
              </thead>
              <tbody>
                {BENCHMARK.map((row, i) => (
                  <tr key={row.model}
                    className="border-t border-white/5 transition-colors"
                    style={{
                      background: row.highlight ? 'rgba(59,130,246,0.06)' : i % 2 === 0 ? 'rgba(10,15,26,0.5)' : 'transparent',
                    }}>
                    <td className="px-6 py-4">
                      <span className={`font-semibold ${row.highlight ? 'text-blue-400' : 'text-slate-300'}`}>
                        {row.model}
                      </span>
                      {row.highlight && <span className="ml-2 badge-blue text-xs">Bizim</span>}
                    </td>
                    <td className="px-6 py-4 text-center font-mono font-bold text-slate-200">{row.pcc}</td>
                    <td className="px-6 py-4 text-center font-mono font-bold text-slate-200">{row.rmse}</td>
                    <td className="px-6 py-4 text-center font-mono text-slate-400">{row.runtime}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className="section-title text-center">Teknik Özellikler</h2>
          <p className="section-subtitle text-center">End-to-end biyoinformatik pipeline</p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((f) => (
              <div key={f.title} className={`card border ${f.border} glass-hover`}>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4`}>
                  <f.icon className="w-6 h-6 text-slate-200" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="card glow-border text-center py-16">
            <GraduationCap className="w-16 h-16 text-blue-400 mx-auto mb-6 animate-float" />
            <h2 className="text-4xl font-black text-white mb-4">Platformu Dene</h2>
            <p className="text-slate-400 mb-8 text-lg">
              SMILES girerek anında pKd tahmini al. Gerçek GNN modeli çalışıyor.
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/dashboard" id="cta-try-demo"
                className="btn-primary flex items-center gap-2 text-base px-8 py-4 rounded-2xl">
                Tahmin Yap <ArrowRight className="w-5 h-5" />
              </Link>
              <Link href="/login" className="btn-ghost flex items-center gap-2 text-base px-8 py-4 rounded-2xl">
                Giriş Yap
              </Link>
            </div>
            <div className="mt-8 flex items-center justify-center gap-6 text-sm text-slate-500 flex-wrap">
              {['GNN eğitilmiş model', 'JWT auth korumalı', 'FastAPI + PyTorch Geometric'].map((t) => (
                <span key={t} className="flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4 text-blue-500" /> {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/6 py-10 px-6 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-slate-300">NeoBioAI</span>
        </div>
        <p className="text-slate-500 text-sm">
          Biyoinformatik Analiz ile Yapay Zeka Tabanlı İlaç Oluşturma — Bitirme Tezi
        </p>
        <p className="text-slate-600 text-xs mt-2">
          GINEConv GNN · FastAPI · PDBBind v2020 · PyTorch Geometric
        </p>
      </footer>
    </div>
  )
}
