# 🎓 NeoBioAI — AI-Powered Drug–Target Affinity Prediction

[![Status](https://img.shields.io/badge/Status-Completed-success)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch%20Geometric-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch-geometric.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Graduation thesis project** — *"Bioinformatics analysis with AI-based drug creation"*
>
> NeoBioAI is an end-to-end full-stack platform that predicts how strongly a small molecule will bind to a target protein using a **Graph Neural Network** (GINEConv) trained on **PDBBind v2020**. Instead of running hours of wet-lab assays or seconds-per-ligand docking, you paste a SMILES string and get a **pKd** prediction, atom-level explanation, AI-written scientific report, and a 3D protein view — in milliseconds.

---

## 🌟 Why It Matters

| Method | Time per molecule |
|---|---|
| Traditional docking (AutoDock Vina) | ~2.5 s |
| **NeoBioAI (GINEConv GNN)** | **~4 ms** |

That is roughly **600× faster** — enabling large virtual screening libraries to be ranked in seconds rather than days.

---

## ✨ Features

| Module | Description |
|---|---|
| 🧠 **GNN Affinity Predictor** | GINEConv graph neural network (~340 k parameters) predicting pKd from SMILES. |
| 🔬 **Atom-Level Explainability** | Integrated Gradients (20-step Riemann approximation) highlights which atoms raise or lower the predicted affinity. |
| 📝 **LLM Report Generation** | Automatic scientific report combining prediction + explanation. OpenAI `gpt-4o-mini` with a deterministic rule-based fallback (always works offline). |
| 🧬 **3D Protein Viewer** | NGL.js-powered interactive visualizer streaming PDB structures directly from RCSB. Cartoon / surface / ball-and-stick modes. |
| 📊 **Batch CSV Inference** | Upload a CSV of SMILES (up to 500 rows) and download predictions as CSV. |
| 📈 **Model Transparency Page** | Full architecture breakdown, hyperparameters, dataset splits, per-epoch training metrics table, and Recharts training curves. |
| 🔐 **Auth & Rate Limiting** | JWT authentication and in-memory rate-limiting middleware on the FastAPI backend. |

---

## 🧪 Model Performance

Trained on a 2 000-complex subset of **PDBBind v2020** (1600 train / 200 val / 200 test), early-stopped after 32 epochs.

| Metric | Value |
|---|---|
| Architecture | GINEConv GNN, 4 layers, hidden_dim = 128 |
| Total parameters | **340 481** |
| Node feature dim | 79 (atom features) |
| Edge feature dim | 10 (bond features) |
| Pooling | mean + max concat |
| **Test RMSE** | **1.5629** |
| **Test Pearson R** | **0.6324** |
| Best Val RMSE | 1.5200 (epoch 17) |
| Training time | 97.2 s (CPU) |

Sample training log (full table available at `/model` in the UI):

```
 Epoch |  Tr MSE | Tr RMSE |  Tr R  | Val MSE | Val RMSE |  Val R |    LR
     1 |  3.7124 |  1.9267 | +0.41  |  3.1684 |   1.7800 | +0.48  | 1.0e-03
    17 |  1.8932 |  1.3760 | +0.71  |  2.3104 |   1.5200 | +0.63  | 5.0e-04  ← best
    32 |  1.6241 |  1.2744 | +0.76  |  2.4421 |   1.5629 | +0.63  | 1.3e-04
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 + Tailwind + Recharts)   :3000        │
│  ┌────────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐        │
│  │ /dashboard │ │  /model  │ │ /batch │ │ /viewer  │        │
│  │ predict +  │ │ epoch    │ │  CSV   │ │   3D     │        │
│  │ explain +  │ │ table +  │ │  bulk  │ │  NGL.js  │        │
│  │ AI report  │ │ charts   │ │        │ │   PDB    │        │
│  └────────────┘ └──────────┘ └────────┘ └──────────┘        │
└───────────────┬─────────────────────────────────────────────┘
                │ REST (JSON)
┌───────────────▼─────────────────────────────────────────────┐
│  Backend (FastAPI + Uvicorn)                   :8000        │
│  /predict /explain /report /batch_csv /model/info /history  │
│     │         │         │                                   │
│     ▼         ▼         ▼                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │   GINEConv GNN (PyTorch Geometric)           │           │
│  │   SMILES → RDKit mol graph → pKd             │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (with `pip`)
- **Node.js 18+** (with `npm`)
- **Git**
- (Optional) `OPENAI_API_KEY` for richer LLM reports — otherwise the rule-based fallback is used automatically.

### 1. Clone

```bash
git clone https://github.com/Taykuth/NeoBioAI.git
cd NeoBioAI
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
cd ..
python -m uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger UI.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev     # uses webpack (Turbopack currently OOMs in Next 16)
```

Open http://localhost:3000.

### 4. One-click launchers (Windows)

```
start_backend.bat
start_frontend.bat
```

Demo account: **`demo@neodock.dev`** / **`demo1234`**

---

## 🧭 UI Pages

| Path | Purpose |
|---|---|
| `/` | Landing page |
| `/login` | JWT auth |
| `/dashboard` | Main prediction — SMILES input, pKd result, **Explain** (atom contributions bar chart), **AI Report** |
| `/model` | **Full model transparency** — stat cards, architecture table, dataset splits, RMSE + Pearson R training curves, per-epoch metrics table |
| `/batch` | CSV upload → bulk predictions CSV download |
| `/viewer` | 3D protein viewer (NGL.js, live PDB from RCSB) with 5 preset proteins |

---

## 🔌 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/predict` | Predict pKd for a SMILES string |
| `POST` | `/explain` | Integrated Gradients atom-level contributions |
| `POST` | `/report` | Combined predict + explain + LLM report |
| `POST` | `/batch_csv` | Bulk CSV inference (≤ 500 rows); streams CSV response with `X-Neo-Success` / `X-Neo-Failed` headers |
| `GET`  | `/model/info` | Architecture, hyperparameters, parameter count, training config |
| `GET`  | `/model/history` | Per-epoch training metrics (MSE, RMSE, Pearson R, R², LR) |
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/docs` | Swagger UI |

### Example

```bash
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"smiles": "CC(=O)Oc1ccccc1C(=O)O"}'
```

```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "pkd": 4.87,
  "affinity": "weak",
  "confidence": 0.81
}
```

---

## 🔬 Try It — Real Molecules

After logging in, enter a SMILES string on the Dashboard:

| Molecule | Use | SMILES | Expected pKd |
|---|---|---|---|
| **Aspirin** | Mild analgesic | `CC(=O)Oc1ccccc1C(=O)O` | ~4.2 (weak) |
| **Ibuprofen** | NSAID | `CC(C)Cc1ccc(cc1)C(C)C(=O)O` | ~5.9 (moderate) |
| **Imatinib** | Anticancer (Gleevec) | `Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C` | ~7.9 (strong / drug-like) |

Higher pKd means stronger binding — and stronger drug potential.

---

## 🔭 Dataset

- **Source:** [PDBBind v2020](http://www.pdbbind.org.cn/) — 19 037 protein–ligand complexes with measured affinities.
- **Subset used:** 2 000 complexes, random split 80 / 10 / 10.
- **Preprocessing:** SMILES → RDKit `Chem.Mol` → PyTorch Geometric `Data(x=[atoms, 79], edge_index, edge_attr=[bonds, 10])`.
- `data/pdbbind/index/INDEX_general_PL.2020` is required to rebuild the cache.

---

## 🗂️ Project Structure

```
neodock/
├── backend/
│   ├── main.py                     # FastAPI app, middleware, lifespan
│   ├── routes/
│   │   ├── predict.py              # POST /predict
│   │   ├── explain.py              # POST /explain  (Integrated Gradients)
│   │   ├── report.py               # POST /report   (LLM + fallback)
│   │   ├── batch_csv.py            # POST /batch_csv
│   │   └── model_info.py           # GET  /model/{info,history}
│   ├── services/
│   │   ├── explain_service.py      # IG implementation
│   │   └── llm_service.py          # OpenAI + rule-based fallback
│   └── requirements.txt
├── frontend/
│   └── src/app/
│       ├── dashboard/              # predict + explain + report
│       ├── model/                  # epoch table + charts
│       ├── batch/                  # CSV bulk inference
│       ├── viewer/                 # NGL.js 3D viewer
│       └── login/                  # JWT auth
├── ml/
│   ├── model_v2.py                 # GINEConv GNN
│   ├── train.py                    # training loop + CSV logger
│   ├── model_info.py               # architecture dump script
│   └── model_final/
│       ├── best_model.pt
│       ├── config.json
│       ├── history.json            # consumed by /model/history
│       └── train_log.csv
├── data/pdbbind/                   # dataset (gitignored)
├── start_backend.bat
├── start_frontend.bat
└── NASIL_CALISTIRILIR.md           # Turkish runbook
```

---

## 🛠️ Tech Stack

**Backend:** Python 3.10 · PyTorch 2 · PyTorch Geometric · RDKit · FastAPI · Uvicorn · python-jose (JWT) · OpenAI SDK
**Frontend:** Next.js 16 · React 19 · Tailwind CSS · Recharts · lucide-react · NGL.js (via CDN)
**ML:** GINEConv · Integrated Gradients · scikit-learn (metrics)

---

## 📚 Thesis Context

This project was developed as a graduation thesis on **"Bioinformatics analysis with AI-based drug creation"**. It demonstrates:

1. An end-to-end ML pipeline from raw public data (PDBBind) to a deployed inference service.
2. Modern graph neural network methods applied to cheminformatics.
3. Explainable AI via Integrated Gradients — making predictions inspectable at the atom level.
4. A production-style full-stack UI suitable for non-expert users (researchers, students).

---

## 📜 License

MIT — see [LICENSE](LICENSE). Free for academic and open-source use with attribution.

## 🙏 Acknowledgements

- [PDBBind](http://www.pdbbind.org.cn/) — benchmark dataset
- [RDKit](https://www.rdkit.org/) — cheminformatics toolkit
- [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/) — GNN framework
- [NGL Viewer](http://nglviewer.org/) — molecular 3D visualization
- [RCSB PDB](https://www.rcsb.org/) — live protein structure source

---

*Developed by **Taykuth** — NeoBioAI Research*
