'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, GraduationCap, Upload, Download, Loader2, CheckCircle, AlertCircle, FileText } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SAMPLE_CSV = `smiles
CC(=O)Oc1ccccc1C(=O)O
CN1C=NC2=C1C(=O)N(C(=O)N2C)C
CC(C)Cc1ccc(cc1)C(C)C(=O)O
O=c1[nH]cc(F)c(=O)[nH]1
Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C`

export default function BatchPage() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [ok, setOk] = useState<{ success: number; failed: number; csv: string; filename: string } | null>(null)

  const upload = async () => {
    if (!file) return
    setLoading(true); setErr(null); setOk(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(`${API_URL}/batch_csv`, { method: 'POST', body: fd })
      if (!res.ok) {
        const j = await res.json().catch(() => ({}))
        throw new Error(j.detail || `HTTP ${res.status}`)
      }
      const csv = await res.text()
      setOk({
        success: Number(res.headers.get('X-Neo-Success') || 0),
        failed:  Number(res.headers.get('X-Neo-Failed')  || 0),
        csv,
        filename: file.name.replace(/\.[^.]+$/, '') + '_predictions.csv',
      })
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const downloadResult = () => {
    if (!ok) return
    const blob = new Blob([ok.csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = ok.filename; a.click()
    URL.revokeObjectURL(url)
  }

  const downloadSample = () => {
    const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'sample.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen molecule-bg" style={{ backgroundColor: '#0a0f1a' }}>
      <header className="border-b border-white/6 px-6 py-4" style={{ background: 'rgba(10,15,26,0.9)' }}>
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Link href="/dashboard" className="text-slate-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></Link>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white">NeoBioAI</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">Batch CSV</span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 space-y-6">
        <div>
          <h1 className="text-3xl font-black text-dark-100 mb-2">Toplu CSV Tahmini</h1>
          <p className="text-dark-300">CSV yükle, her satır için SMILES tahmin al, sonuç CSV'yi indir. (max 500 satır)</p>
        </div>

        <div className="card">
          <h3 className="font-semibold text-dark-200 mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400"/> CSV Formatı
          </h3>
          <pre className="bg-dark-900 rounded p-3 text-xs font-mono text-dark-300 overflow-x-auto">{SAMPLE_CSV}</pre>
          <button onClick={downloadSample} className="btn-ghost mt-3 text-xs flex items-center gap-2">
            <Download className="w-3 h-3" /> Örnek CSV indir
          </button>
        </div>

        <div className="card">
          <label className="flex flex-col items-center justify-center gap-3 py-10 rounded-lg cursor-pointer transition-all"
            style={{ border: '2px dashed rgba(59,130,246,0.3)', background: 'rgba(59,130,246,0.03)' }}>
            <Upload className="w-10 h-10 text-blue-400" />
            <div className="text-center">
              <div className="text-dark-200 font-semibold">
                {file ? file.name : 'CSV dosyası seç'}
              </div>
              <div className="text-dark-400 text-xs mt-1">
                {file ? `${(file.size/1024).toFixed(1)} KB` : '.csv veya .txt — tek SMILES kolonu'}
              </div>
            </div>
            <input type="file" accept=".csv,.txt" className="hidden"
              onChange={e => { setFile(e.target.files?.[0] || null); setOk(null); setErr(null) }} />
          </label>

          <button onClick={upload} disabled={!file || loading}
            className="btn-primary w-full mt-4 flex items-center justify-center gap-2">
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> İşleniyor (bu biraz sürebilir)...</>
              : <><Upload className="w-4 h-4" /> Yükle ve Tahmin Et</>}
          </button>
        </div>

        {err && (
          <div className="card border border-red-500/30" style={{ background: 'rgba(239,68,68,0.05)' }}>
            <div className="flex gap-3 items-start">
              <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
              <div><h4 className="font-semibold text-red-400">Hata</h4><p className="text-sm text-dark-300">{err}</p></div>
            </div>
          </div>
        )}

        {ok && (
          <div className="card border border-green-500/30" style={{ background: 'rgba(34,197,94,0.05)' }}>
            <div className="flex gap-3 items-start mb-4">
              <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-green-400 mb-1">Tahmin Tamamlandı</h4>
                <p className="text-sm text-dark-300">Başarılı: <strong>{ok.success}</strong> · Başarısız: <strong>{ok.failed}</strong></p>
              </div>
              <button onClick={downloadResult} className="btn-primary flex items-center gap-2 text-xs px-4 py-2">
                <Download className="w-3 h-3" /> CSV İndir
              </button>
            </div>
            <pre className="bg-dark-900 rounded p-3 text-xs font-mono text-dark-300 max-h-64 overflow-auto">{ok.csv}</pre>
          </div>
        )}
      </main>
    </div>
  )
}
