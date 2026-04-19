'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, GraduationCap, Box, Search, Loader2, Info } from 'lucide-react'

const PRESETS = [
  { id: '1HEW', name: 'Human lysozyme',  desc: 'Klasik test protein' },
  { id: '3ERT', name: 'Estrogen Receptor',desc: 'Tamoksifen kompleksi' },
  { id: '1CBS', name: 'Retinol binding', desc: 'Kucuk ligand taniyici' },
  { id: '2IKO', name: 'Imatinib/ABL',    desc: 'Gleevec hedef proteini' },
  { id: '1FKB', name: 'FKBP12',          desc: 'FK506 kompleksi' },
]

export default function ViewerPage() {
  const containerRef = useRef<HTMLDivElement>(null)
  const stageRef = useRef<any>(null)
  const [pdbId, setPdbId] = useState('1HEW')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [status, setStatus] = useState('')
  const [repr, setRepr] = useState<'cartoon' | 'surface' | 'ball+stick'>('cartoon')

  // NGL'i CDN'den yukle
  useEffect(() => {
    if (typeof window === 'undefined') return
    if ((window as any).NGL) { initStage(); return }
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/ngl@2.3.1/dist/ngl.js'
    script.async = true
    script.onload = () => initStage()
    script.onerror = () => setErr('NGL yuklenmedi (ag yok?)')
    document.body.appendChild(script)
    return () => { script.parentNode?.removeChild(script) }
  }, [])

  const initStage = () => {
    if (!containerRef.current || stageRef.current) return
    const NGL = (window as any).NGL
    const stage = new NGL.Stage(containerRef.current, { backgroundColor: '#0a0f1a' })
    stageRef.current = stage
    loadPDB(pdbId)
    window.addEventListener('resize', () => stage.handleResize())
  }

  const loadPDB = async (id: string) => {
    const stage = stageRef.current
    if (!stage) return
    setLoading(true); setErr(null); setStatus('')
    try {
      stage.removeAllComponents()
      const comp = await stage.loadFile(`rcsb://${id}.pdb`, { defaultRepresentation: false })
      comp.addRepresentation(repr, { colorScheme: 'chainindex' })
      comp.addRepresentation('ball+stick', { sele: 'hetero and not water', colorScheme: 'element' })
      comp.autoView()
      setStatus(`PDB ${id.toUpperCase()} yuklendi.`)
    } catch (e: any) {
      setErr(`PDB ${id} yuklenemedi: ${e?.message || e}`)
    } finally { setLoading(false) }
  }

  const changeRepr = (r: typeof repr) => {
    setRepr(r)
    const stage = stageRef.current
    if (!stage) return
    stage.eachComponent((c: any) => {
      c.removeAllRepresentations()
      c.addRepresentation(r, { colorScheme: 'chainindex' })
      c.addRepresentation('ball+stick', { sele: 'hetero and not water', colorScheme: 'element' })
    })
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0a0f1a' }}>
      <header className="border-b border-white/6 px-6 py-4" style={{ background: 'rgba(10,15,26,0.9)' }}>
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Link href="/dashboard" className="text-slate-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></Link>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e3a5f, #2563eb)' }}>
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white">NeoBioAI</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">3D Viewer</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 grid lg:grid-cols-[1fr_320px] gap-6">
        <div className="space-y-3">
          <div className="card p-2">
            <div ref={containerRef} style={{ width: '100%', height: '72vh', borderRadius: '8px', overflow: 'hidden' }} />
          </div>
          {status && <p className="text-xs text-green-400">{status}</p>}
          {err    && <p className="text-xs text-red-400">{err}</p>}
        </div>

        <aside className="space-y-5">
          <div className="card">
            <h3 className="font-semibold text-dark-200 mb-3 flex items-center gap-2">
              <Search className="w-4 h-4 text-blue-400"/> PDB ID
            </h3>
            <div className="flex gap-2">
              <input className="input-field font-mono uppercase" placeholder="1HEW"
                value={pdbId} onChange={e => setPdbId(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && loadPDB(pdbId)} />
              <button className="btn-primary text-sm px-4" disabled={loading}
                onClick={() => loadPDB(pdbId)}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Yukle'}
              </button>
            </div>
            <p className="text-xs text-dark-400 mt-2">RCSB veritabanindan canli cekilir.</p>
          </div>

          <div className="card">
            <h3 className="font-semibold text-dark-200 mb-3">Temsil Modu</h3>
            <div className="grid grid-cols-3 gap-2">
              {(['cartoon','surface','ball+stick'] as const).map(r => (
                <button key={r} onClick={() => changeRepr(r)}
                  className={`text-xs px-3 py-2 rounded border transition-all
                    ${repr === r ? 'border-blue-500 bg-blue-500/10 text-blue-300' : 'border-white/10 text-dark-300 hover:border-white/20'}`}>
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-dark-200 mb-3 flex items-center gap-2">
              <Box className="w-4 h-4 text-purple-400"/> Hazir Proteinler
            </h3>
            <div className="space-y-2">
              {PRESETS.map(p => (
                <button key={p.id} onClick={() => { setPdbId(p.id); loadPDB(p.id) }}
                  className="w-full text-left px-3 py-2 rounded border border-white/10 hover:border-white/25 transition">
                  <div className="flex justify-between">
                    <span className="font-mono text-sm text-blue-300">{p.id}</span>
                    <span className="text-xs text-dark-400">{p.desc}</span>
                  </div>
                  <div className="text-xs text-dark-300">{p.name}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="card flex gap-3 items-start">
            <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5"/>
            <p className="text-xs text-dark-300 leading-relaxed">
              Mouse: sol-tık döndür, sağ-tık kaydır, tekerlek zoom. Heteroatomlar (ligandlar) otomatik olarak ball+stick ile gösterilir.
            </p>
          </div>
        </aside>
      </main>
    </div>
  )
}
