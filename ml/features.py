"""
Neo-Dock — ml/features.py
============================
SMILES → PyTorch Geometric Data dönüşümü.

Atom özellikleri (79 boyut):
  - Atom tipi (one-hot, 44)
  - Derece (one-hot, 11)  
  - Implisit H sayısı (one-hot, 9)
  - Formal yük (one-hot, 5)
  - Hibridizasyon (one-hot, 6)
  - Aromatiklik (1 bool)
  - Ring üyesi (1 bool)
  - Chiralite (one-hot, 3)

Bağ özellikleri (10 boyut):
  - Bağ tipi (one-hot, 4)
  - Konjuge (1)
  - Ring (1)
  - Stereo (one-hot, 4)
"""

import torch
import numpy as np
from torch_geometric.data import Data


# ─── Atom özellik listeleri ────────────────────────────────

ATOM_TYPES = [
    "C", "N", "O", "S", "F", "Si", "P", "Cl", "Br", "Mg",
    "Na", "Ca", "Fe", "As", "Al", "I", "B", "V", "K", "Tl",
    "Yb", "Sb", "Sn", "Ag", "Pd", "Co", "Se", "Ti", "Zn",
    "H", "Li", "Ge", "Cu", "Au", "Ni", "Cd", "In", "Mn",
    "Zr", "Cr", "Pt", "Hg", "Pb", "Unknown",
]

HYBRIDIZATION = [
    "S", "SP", "SP2", "SP3", "SP3D", "SP3D2",
]

BOND_TYPES = ["SINGLE", "DOUBLE", "TRIPLE", "AROMATIC"]

STEREO_TYPES = ["STEREONONE", "STEREOANY", "STEREOZ", "STEREOE"]


def _one_hot(val, choices: list) -> list:
    vec = [0] * len(choices)
    if val in choices:
        vec[choices.index(val)] = 1
    else:
        vec[-1] = 1
    return vec


def atom_features(atom) -> list:
    from rdkit.Chem import rdchem
    feats = []
    feats += _one_hot(atom.GetSymbol(), ATOM_TYPES)
    feats += _one_hot(atom.GetDegree(), list(range(11)))
    feats += _one_hot(atom.GetTotalNumHs(), list(range(9)))
    feats += _one_hot(atom.GetFormalCharge(), [-2, -1, 0, 1, 2])
    feats += _one_hot(
        atom.GetHybridization().name,
        HYBRIDIZATION,
    )
    feats.append(int(atom.GetIsAromatic()))
    feats.append(int(atom.IsInRing()))
    feats += _one_hot(
        atom.GetChiralTag().name,
        ["CHI_UNSPECIFIED", "CHI_TETRAHEDRAL_CW", "CHI_TETRAHEDRAL_CCW"],
    )
    return feats


def bond_features(bond) -> list:
    feats = []
    feats += _one_hot(bond.GetBondTypeAsDouble(),
                      [1.0, 1.5, 2.0, 3.0])   # SINGLE/AROMATIC/DOUBLE/TRIPLE
    feats.append(int(bond.GetIsConjugated()))
    feats.append(int(bond.IsInRing()))
    feats += _one_hot(bond.GetStereo().name, STEREO_TYPES)
    return feats


def smiles_to_graph(smiles: str) -> Data:
    """SMILES string → PyG Data nesnesi."""
    from rdkit import Chem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Geçersiz SMILES: {smiles}")

    # Atom özellikleri
    atom_feats = [atom_features(a) for a in mol.GetAtoms()]
    x = torch.tensor(atom_feats, dtype=torch.float)

    # Bağ özellikleri + kenar listesi
    if mol.GetNumBonds() == 0:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr  = torch.zeros((0, 10), dtype=torch.float)
    else:
        rows, cols, bond_feats = [], [], []
        for bond in mol.GetBonds():
            i = bond.GetBeginAtomIdx()
            j = bond.GetEndAtomIdx()
            bf = bond_features(bond)
            rows += [i, j]
            cols += [j, i]
            bond_feats += [bf, bf]   # çift yönlü

        edge_index = torch.tensor([rows, cols], dtype=torch.long)
        edge_attr  = torch.tensor(bond_feats, dtype=torch.float)

    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


# ─── Boyut sabitler ───────────────────────────────────────

NODE_DIM = len(atom_features(
    __import__("rdkit.Chem", fromlist=["Chem"]).MolFromSmiles("C").GetAtomWithIdx(0)
)) if True else 79    # 79

EDGE_DIM = len(bond_features(
    __import__("rdkit.Chem", fromlist=["Chem"]).MolFromSmiles("CC").GetBondWithIdx(0)
)) if True else 10    # 10
