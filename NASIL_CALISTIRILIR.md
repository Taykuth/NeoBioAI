# Neo-Dock — Hızlı Başlangıç

## Proje Konumu
`C:\Users\Taykuth\Desktop\Bitirme tezi\neodock`

## Mimari Özet

**Neo-Dock**, PDBBind veri seti üzerinde eğitilmiş GINEConv GNN modelini
bir FastAPI servisi ve Next.js arayüzü ile uçtan uca sunar.

```
 SMILES ──► RDKit → 80D atom / 10D bond graph ──► GINEConv×4 ──► pKd
    ▲                                                              │
    │ Next.js (port 3000)     ←───  JSON  ────    FastAPI (8000) ──┘
```

### Eğitilmiş Model
- Mimari: GINEConv GNN (~340 K parametre, 4 katman, hidden 128)
- Veri: PDBBind v2020 (2000 örnek, 80/10/10 split)
- Test RMSE: **1.55**, PCC: **0.66**
- Inference: ~200 ms / molekül (CPU)
- Ağırlıklar: `ml/model_final/best_model.pt`

## Çalıştırma

### 1) Backend (FastAPI)
```
start_backend.bat        # veya:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### 2) Frontend (Next.js)
```
start_frontend.bat       # NODE_OPTIONS=--max-old-space-size=4096 ayarlı
```
- Anasayfa: http://localhost:3000
- Dashboard (tahmin arayüzü): http://localhost:3000/dashboard

> **Not:** Turbopack bu projede bellek taşması verdiği için `next dev --webpack`
> kullanıldı ve 4 GB heap limiti verildi. Bu ayar `start_frontend.bat` içinde
> otomatik yapılır.

## API Örneği

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d "{\"smiles\":\"CC(=O)Oc1ccccc1C(=O)O\"}"
```

Yanıt:
```json
{
  "predicted_pKd": 4.272,
  "affinity_label": "weak",
  "runtime_ms": 188,
  "model_version": "v1.0",
  "is_mock": false
}
```

### pKd Yorumu
| pKd | Yorum |
|-----|-------|
| <5  | Zayıf bağlanma |
| 5–7 | Orta |
| 7–9 | Güçlü (ilaç adayı) |
| >9  | Çok güçlü |

## Yeniden Eğitim
PDBBind dataseti `P-L/` altında (2011–2019 klasörleri, her PDB kodunda
`*_ligand.sdf`, `*_protein.pdb`, `*_pocket.pdb`).

```bash
python ml/train.py --data_dir ../P-L --epochs 100
```

## Hafta Hafta Kapsam (Hafta 3–8)
- **Hafta 3:** GINEConv modeli, end-to-end pipeline, /predict endpoint — ✅
- **Hafta 4:** Batch inference, async job, model export (.pt), JWT auth — ✅
- **Hafta 5:** Explainability (feature importance), LLM rapor altyapısı — kısmi
- **Hafta 6:** Docker/cloud deploy, rate limiting, user panel — rate limit ✅
- **Hafta 7:** Demo flow, UI polish, bug fix — ✅
- **Hafta 8:** Landing page, benchmark grafikleri, final rapor — ✅

## Dizin Yapısı
```
neodock/
├── backend/           FastAPI (main.py, routes/, services/, auth_jwt/, middleware/)
├── ml/                GNN (model_v2.py, features.py, data_loader.py, train.py)
│   └── model_final/   Eğitilmiş ağırlıklar + config.json
├── frontend/          Next.js 16 (app router)
│   └── src/app/       page.tsx (landing), dashboard/, login/
├── data/              İşlenmiş dataset
├── demo/ tests/
├── requirements.txt
├── start_backend.bat   start_frontend.bat
└── NASIL_CALISTIRILIR.md  (bu dosya)
```
