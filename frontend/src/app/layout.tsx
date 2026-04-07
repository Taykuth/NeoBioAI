import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'NeoBioAI — Yapay Zeka Tabanlı İlaç Keşif Platformu',
  description: 'GINEConv tabanlı Graf Sinir Ağı ile protein-ligand bağlanma afinitesi (pKd) tahmini. Biyoinformatik analiz ve yapay zeka tabanlı ilaç geliştirme platformu.',
  keywords: ['molecular docking', 'drug discovery', 'GNN', 'bioinformatics', 'AI', 'pKd prediction', 'NeoBioAI'],
  authors: [{ name: 'NeoBioAI' }],
  openGraph: {
    title: 'NeoBioAI — Yapay Zeka Tabanlı İlaç Keşif Platformu',
    description: 'GINEConv GNN ile protein-ligand bağlanma afinitesi tahmini',
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
