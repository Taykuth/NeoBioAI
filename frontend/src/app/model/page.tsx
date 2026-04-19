'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, GraduationCap, Atom, TrendingUp, Clock } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ModelInfo = {
  version: string; architecture: string; hidden_dim: number; n_layers: number
  dropout: number; node_dim: number; edge_dim: number; pooling: string
  total_parameters: number
  dataset: { name: string; train: number; val: number; test: number }
  training: { epochs_trained: number; train_time_s: number; best_val_rmse: number; test_rmse: number; test_pcc: number }
}
type HistoryRow = {
  epoch: number; tr_mse: number; tr_rmse: number; tr_pcc: number; tr_r2: number
  val_mse: number; val_rmse: number; val_pcc: number; val_r2: number; lr: number
}

export default function ModelPage() {
  const [info, setInfo] = useState<ModelInfo | null>(null)
  const [history, setHistory] = useState<HistoryRow[]>([])
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        const i = await fetch(`${API_URL}/model/info`).then(r => r.json())
        setInfo(i)
        const h = await fetch(`${API_URL}/model/history`).then(r => r.json())
        setHistory(h.history || [])
      } catch (e: any) { setErr(e.message) }
    })()
  }, [])

  return (
    <div className="min-h-screen molecule-bg" style={{ backgroundColor: '#0a0f1a' }}>
      <header className="border-b border-white/6 px-6 py-4" style={{ background: 'rgba(10,15,26,0.9)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></Link>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
                <GraduationCap className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-white">NeoBioAI</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-400">Model</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10 space-y-8">
        <div>
          <h1 className="text-3xl font-black text-dark-100 mb-2">Model Detayları</h1>
          <p className="text-dark-300">GINEConv GNN mimarisi, parametreler ve epoch-bazlı eğitim metrikleri.</p>
        </div>

        {err && <div className="card border border-red-500/30 text-red-300">{err}</div>}

        {info && (
          <>
            <div className="grid md:grid-cols-4 gap-4">
              {[
                { icon: Atom, label: 'Parametre', value: info.total_parameters?.toLocaleString() || '—' },
                { icon: TrendingUp, label: 'Test PCC', value: info.training.test_pcc?.toFixed(4) || '—' },
                { icon: TrendingUp, label: 'Test RMSE', value: info.training.test_rmse?.toFixed(4) || '—' },
                { icon: Clock, label: 'Eğitim Süresi', value: `${info.training.train_time_s?.toFixed(1)}s` },
              ].map((s, i) => (
                <div key={i} className="card">
                  <s.icon className="w-5 h-5 text-blue-400 mb-2" />
                  <div className="text-2xl font-black text-dark-100">{s.value}</div>
                  <div className="text-xs text-dark-400 mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="font-semibold text-dark-200 mb-4">Mimari</h3>
                <div className="space-y-2 text-sm">
                  {[
                    ['Tip', info.architecture],
                    ['Version', info.version],
                    ['Hidden dim', info.hidden_dim],
                    ['GINE Katman', info.n_layers],
                    ['Dropout', info.dropout],
                    ['Node (atom) dim', info.node_dim],
                    ['Edge (bond) dim', info.edge_dim],
                    ['Pooling', info.pooling],
                  ].map(([k, v]) => (
                    <div key={k as string} className="flex justify-between border-b border-white/5 py-1.5">
                      <span className="text-dark-400">{k}</span>
                      <span className="font-mono text-dark-100">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h3 className="font-semibold text-dark-200 mb-4">Dataset & Eğitim</h3>
                <div className="space-y-2 text-sm">
                  {[
                    ['Dataset', info.dataset.name],
                    ['Train', info.dataset.train],
                    ['Validation', info.dataset.val],
                    ['Test', info.dataset.test],
                    ['Epochs trained', info.training.epochs_trained],
                    ['Best Val RMSE', info.training.best_val_rmse?.toFixed(4)],
                    ['Test RMSE', info.training.test_rmse?.toFixed(4)],
                    ['Test PCC (Pearson R)', info.training.test_pcc?.toFixed(4)],
                  ].map(([k, v]) => (
                    <div key={k as string} className="flex justify-between border-b border-white/5 py-1.5">
                      <span className="text-dark-400">{k}</span>
                      <span className="font-mono text-dark-100">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {history.length > 0 && (
          <>
            <div className="card">
              <h3 className="font-semibold text-dark-200 mb-4">Eğitim Eğrisi (RMSE)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="epoch" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                  <Legend />
                  <Line type="monotone" dataKey="tr_rmse" stroke="#3b82f6" name="Train RMSE" dot={false} />
                  <Line type="monotone" dataKey="val_rmse" stroke="#ef4444" name="Val RMSE" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold text-dark-200 mb-4">Pearson R (Correlation)</h3>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="epoch" stroke="#64748b" />
                  <YAxis stroke="#64748b" domain={[0, 1]} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
                  <Legend />
                  <Line type="monotone" dataKey="tr_pcc" stroke="#22c55e" name="Train R" dot={false} />
                  <Line type="monotone" dataKey="val_pcc" stroke="#eab308" name="Val R" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card overflow-x-auto">
              <h3 className="font-semibold text-dark-200 mb-4">Epoch Tablosu</h3>
              <table className="w-full text-xs font-mono">
                <thead className="text-dark-400 border-b border-white/10">
                  <tr>
                    <th className="text-left py-2 pr-4">Epoch</th>
                    <th className="text-right pr-4">Tr MSE</th>
                    <th className="text-right pr-4">Tr RMSE</th>
                    <th className="text-right pr-4">Tr R</th>
                    <th className="text-right pr-4">Val MSE</th>
                    <th className="text-right pr-4">Val RMSE</th>
                    <th className="text-right pr-4">Val R</th>
                    <th className="text-right">LR</th>
                  </tr>
                </thead>
                <tbody className="text-dark-200">
                  {history.map((r) => (
                    <tr key={r.epoch} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-1.5 pr-4">{r.epoch}</td>
                      <td className="text-right pr-4">{r.tr_mse?.toFixed(4)}</td>
                      <td className="text-right pr-4">{r.tr_rmse?.toFixed(4)}</td>
                      <td className="text-right pr-4">{r.tr_pcc >= 0 ? '+' : ''}{r.tr_pcc?.toFixed(4)}</td>
                      <td className="text-right pr-4">{r.val_mse?.toFixed(4)}</td>
                      <td className="text-right pr-4">{r.val_rmse?.toFixed(4)}</td>
                      <td className="text-right pr-4">{r.val_pcc >= 0 ? '+' : ''}{r.val_pcc?.toFixed(4)}</td>
                      <td className="text-right">{r.lr?.toExponential(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
