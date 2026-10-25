# NeoBioAI — Binding Affinity Prediction from Ligand Structure

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch Geometric](https://img.shields.io/badge/ML-PyTorch%20Geometric-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch-geometric.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Graduation thesis, B.Sc. Artificial Intelligence Engineering, OSTİM Technical University (2026). Thesis title: *Bioinformatics analysis with AI-based drug creation*.

NeoBioAI takes a molecule as a SMILES string, turns it into an atom-bond graph and predicts its binding affinity (pKd) with a GINEConv graph neural network trained on PDBBind v2020. The model is served through a FastAPI backend and a Next.js interface with atom-level explanations, batch CSV scoring and an LLM-written summary report.

> **Main limitation, stated up front:** the model only sees the ligand. It has no input for the target protein, so it predicts one pKd per molecule regardless of which protein it binds to. See [What the model does not do](#what-the-model-does-not-do).

## Results

Trained on a 2,000-complex subset of PDBBind v2020 with a random 80/10/10 split (1,600 / 200 / 200). Numbers are from `ml/model_final/config.json` and `ml/model_final/train_log.csv`.

| Metric | Value |
| --- | --- |
| Test RMSE (pKd units) | **1.563** |
| Test Pearson r | **0.632** |
| Best validation RMSE | 1.515 (epoch 17) |
| Epochs trained | 32 (early stopping) |
| Training time | 97 s on CPU |
| Parameters | 340,481 |
| Inference latency | 3.8 ms median per molecule (SMILES → graph → prediction, 1 CPU thread) |
| Batch inference | 500 molecules in ~0.2 s |

Latency was measured by loading `ml/model_final/best_model.pt` and timing 200 single-molecule predictions.

Excerpt from the real training log:

```
epoch  tr_rmse  tr_r    val_rmse  val_r   lr
    1   1.927   0.390    1.780   0.471   1.0e-03
   17   1.507   0.688    1.515   0.647   1.0e-03   <- best validation
   32   1.426   0.779    1.688   0.617   5.0e-04
```

The gap between training and validation after epoch 17 shows the model starting to overfit on a small dataset.

## What the model does not do

- **No protein input.** `ml/model_v2.py` has a `use_pocket` flag, but the forward pass never uses protein or pocket features. The `pdb_id` field on `/predict` is accepted and ignored. A real drug–target model needs the protein (sequence embeddings or a pocket graph).
- **Not comparable to docking or published benchmarks.** An earlier version of this README compared speed against AutoDock Vina and listed literature scores. Vina searches binding poses inside a given protein pocket; this model does not. Published PDBBind results are usually reported on the CASF core set with protein structures. Those comparisons were removed.
- **Optimistic split.** A random split lets very similar molecules appear in both train and test. A scaffold split or the CASF-2016 core set would give a harder, more honest number.
- **No baseline.** There is no comparison against a simple model such as a random forest on molecular fingerprints, so it is not yet shown that the GNN adds value. PDBBind is known to reward ligand-only models more than it should, which is a dataset-bias problem discussed in the literature.
- **No uncertainty estimate.** The API returns `confidence: 0.0` because no uncertainty method is implemented.
- **Mock fallback.** If the model file cannot be loaded, the backend returns a deterministic placeholder value with `is_mock: true`.

## Features

| Module | What it does |
| --- | --- |
| GNN predictor | 4-layer GINEConv with residual connections, mean + max pooling, MLP head. 80 atom features, 10 bond features (RDKit). |
| Atom-level explanation | Integrated Gradients (20 steps) over atom features: which atoms push the prediction up or down. |
| LLM report | Short report from the prediction and explanation with OpenAI `gpt-4o-mini`, with a rule-based fallback when no API key is set. LLM text is not checked for scientific accuracy. |
| Batch CSV | Upload up to 500 SMILES, download predictions as CSV. |
| Model page | Architecture, hyperparameters, dataset split and per-epoch curves from the saved training history. |
| 3D viewer | NGL.js viewer that loads PDB structures from RCSB. For visualization only; the structure is not a model input. |
| Demo auth | JWT tokens and a per-IP rate limit (60 requests/minute). Users are kept in memory with unsalted SHA-256 hashes, which is fine for a demo and not for production. |

## Architecture

```
Next.js (dashboard, model, batch, viewer)
        │  REST / JSON
FastAPI backend
  /predict  /explain  /report  /batch_csv  /model/info  /model/history  /health
        │
SMILES → RDKit mol → PyG graph (80-d atoms, 10-d bonds)
       → 4 × GINEConv (+ residual, LayerNorm) → mean ‖ max pool → MLP → pKd
```

## Run locally

Requirements: Python 3.10+, Node.js 18+. The trained model is included in `ml/model_final/`, so the dataset is only needed for retraining.

```bash
git clone https://github.com/Taykuth/NeoBioAI.git
cd NeoBioAI

# backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000   # Swagger UI at http://localhost:8000/docs

# frontend (second terminal)
cd frontend
npm install
npm run dev    # http://localhost:3000
```

Windows users can run `start_backend.bat` and `start_frontend.bat`. A Turkish step-by-step guide is in `NASIL_CALISTIRILIR.md`. Demo login: `demo@neodock.dev` / `demo1234`. `OPENAI_API_KEY` is optional.

### Example request

```bash
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"smiles": "CC(=O)Oc1ccccc1C(=O)O"}'
```

```json
{
  "predicted_pKd": 4.634,
  "confidence": 0.0,
  "runtime_ms": 3.9,
  "model_version": "v1.0",
  "is_mock": false,
  "error": null,
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "affinity_label": "weak",
  "user_tier": "guest"
}
```

Model outputs for three well-known drugs (no target protein involved): aspirin 4.63, ibuprofen 5.70, imatinib 7.47.

### Retraining

Training needs PDBBind v2020 (free registration at pdbbind.org.cn) with `INDEX_general_PL.2020` in `data/pdbbind/index/`. The training script is `ml/train.py`.

## Project structure

```
NeoBioAI/
├── backend/            FastAPI app: routes/, services/ (ml, explain, llm), auth_jwt/, middleware/
├── frontend/src/app/   Next.js pages: dashboard, model, batch, viewer, login
├── ml/
│   ├── features.py     SMILES → PyG graph
│   ├── model_v2.py     GINEConv model
│   ├── train.py        training loop, split, CSV logging
│   └── model_final/    best_model.pt, config.json, history.json, train_log.csv
├── demo/jury_demo.py   script used for the thesis presentation
├── tests/test_api.py   integration checks against a running backend
└── NASIL_CALISTIRILIR.md
```

## Next steps

1. Add the protein: per-residue embeddings from a protein language model, or a pocket graph built from the PDBBind complex.
2. Evaluate on a scaffold split and on the CASF-2016 core set.
3. Add baselines (fingerprint + random forest, ligand-only vs. protein-aware) to show what each part contributes.
4. Train on the full refined set instead of 2,000 complexes.
5. Replace `confidence: 0.0` with a real uncertainty estimate (ensembles or MC dropout).

## Acknowledgements

[PDBBind](http://www.pdbbind.org.cn/) · [RDKit](https://www.rdkit.org/) · [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/) · [NGL Viewer](http://nglviewer.org/) · [RCSB PDB](https://www.rcsb.org/)

MIT License, see [LICENSE](LICENSE).
