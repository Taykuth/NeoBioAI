"""
Neo-Dock -- backend/services/explain_service.py
================================================
Atom-seviye explainability: Integrated Gradients + Masking.

SMILES -> graf oluştur, her atomun pKd'ye katkısını hesapla.
Cikti: atom_idx -> (symbol, contribution, SMILES konumu).

Algoritma (Integrated Gradients):
  phi_i = (x_i - baseline_i) * integral(grad of f wrt x at alpha*x) d_alpha
  Basit 20 adimli Riemann toplami ile yaklastik.
"""

from __future__ import annotations
from typing import Optional
import numpy as np


def _top_k_atoms(contribs: np.ndarray, atoms: list, k: int = 8) -> list:
    """En yuksek |katki| degerine sahip k atomu dondur."""
    abs_rank = np.argsort(-np.abs(contribs))
    out = []
    for idx in abs_rank[:k]:
        out.append({
            "atom_idx":     int(idx),
            "symbol":       atoms[idx],
            "contribution": float(contribs[idx]),
            "direction":    "artirir" if contribs[idx] > 0 else "azaltir",
        })
    return out


def explain(smiles: str, steps: int = 20, top_k: int = 8) -> dict:
    """
    SMILES -> atom-seviye katki skoru.
    Model mock modda veya yuklenmemisse basit heuristic fallback uretir.
    """
    try:
        from backend.services.ml_service import _model, _device, _load_model
    except Exception as e:
        return {"error": f"ml_service import hatasi: {e}"}

    # Modeli hazirla
    if _model is None:
        _load_model()
    from backend.services import ml_service as S
    model = S._model
    device = S._device

    try:
        from rdkit import Chem
        from ml.features import smiles_to_graph
    except Exception as e:
        return {"error": f"RDKit/features import hatasi: {e}"}

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"error": "Gecersiz SMILES"}

    atoms = [a.GetSymbol() for a in mol.GetAtoms()]
    n_atoms = len(atoms)

    if model is None:
        # Mock fallback: C < N < O < F < hetero sirasi
        weights = {"C": 0.1, "N": 0.25, "O": 0.35, "F": 0.2, "Cl": 0.25,
                   "Br": 0.3, "S": 0.3, "P": 0.4, "N+": 0.5}
        contribs = np.array([weights.get(s, 0.15) for s in atoms])
        return {
            "is_mock":    True,
            "n_atoms":    n_atoms,
            "atoms":      atoms,
            "contribs":   contribs.tolist(),
            "top_atoms":  _top_k_atoms(contribs, atoms, top_k),
            "method":     "heuristic_mock",
        }

    import torch
    graph = smiles_to_graph(smiles)
    batch = torch.zeros(graph.x.shape[0], dtype=torch.long)

    # Integrated Gradients
    x_input  = graph.x.clone().float().to(device).requires_grad_(True)
    baseline = torch.zeros_like(x_input).to(device)
    edge_index = graph.edge_index.to(device)
    edge_attr  = graph.edge_attr.to(device).float()
    batch_dev  = batch.to(device)

    integrated = torch.zeros_like(x_input)
    for step in range(1, steps + 1):
        alpha = step / steps
        x_interp = (baseline + alpha * (x_input - baseline)).detach().requires_grad_(True)

        # Modeli çağırmak için Data-benzeri obje
        class _Mini:
            def __init__(self, x, edge_index, edge_attr, batch):
                self.x = x
                self.edge_index = edge_index
                self.edge_attr  = edge_attr
                self.batch      = batch

        out = model(_Mini(x_interp, edge_index, edge_attr, batch_dev)).squeeze()
        grad = torch.autograd.grad(out, x_interp, create_graph=False)[0]
        integrated += grad

    integrated = integrated / steps
    ig = (x_input - baseline) * integrated     # (n_atoms, feat_dim)
    # Her atom icin feature'lar boyunca topla
    contribs = ig.sum(dim=1).detach().cpu().numpy()

    return {
        "is_mock":   False,
        "method":    "integrated_gradients",
        "steps":     steps,
        "n_atoms":   n_atoms,
        "atoms":     atoms,
        "contribs":  contribs.tolist(),
        "top_atoms": _top_k_atoms(contribs, atoms, top_k),
    }
