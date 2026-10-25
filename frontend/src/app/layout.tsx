import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NeoBioAI — Yapay Zeka Tabanlı İlaç Keşif Platformu',
  description: 'GINEConv tabanlı Graf Sinir Ağı ile ligand yapısından bağlanma afinitesi (pKd) tahmini. Yapay zeka mühendisliği bitirme tezi.',
  keywords: ['drug discovery', 'GNN', 'bioinformatics', 'cheminformatics', 'pKd prediction', 'NeoBioAI'],
  authors: [{ name: 'NeoBioAI' }],
  openGraph: {
    title: 'NeoBioAI — Yapay Zeka Tabanlı İlaç Keşif Platformu',
    description: 'GINEConv GNN ile ligand tabanlı bağlanma afinitesi tahmini',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  )
}
