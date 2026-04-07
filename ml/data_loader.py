"""
Neo-Dock — ml/data_loader.py
==============================
PDBBind veri seti yukleme ve on-isleme araclari.

Desteklenen formatlar:
  - PDBBind v2020.R1 (Demo)
  - PDBBind v2016 (refined/core)

Kullanim:
  from ml.data_loader import PDBBindDataset
  dataset = PDBBindDataset("data/pdbbind")
"""

import os
import logging
from pathlib import Path
from typing import Optional

import torch
import numpy as np
from torch_geometric.data import Dataset, Data

logger = logging.getLogger(__name__)


class PDBBindDataset(Dataset):
    """
    PDBBind veri setini PyG Dataset olarak yukler.
    Lazy loading: her __getitem__ cagirisinda SDF->Graph donusumu yapar.
    Buyuk datasetler icin bellek tasarrufu saglar.
    """

    def __init__(self, root: str, index_file: Optional[str] = None,
                 transform=None, pre_transform=None):
        self.data_root = Path(root)
        self._index_file = index_file
        self._entries = []
        self._find_index_and_parse()
        super().__init__(str(self.data_root), transform, pre_transform)

    def _find_index_and_parse(self):
        """Index dosyasini bul ve parse et."""
        if self._index_file and Path(self._index_file).exists():
            index_path = Path(self._index_file)
        else:
            # Otomatik arama
            candidates = list(self.data_root.rglob("INDEX*PL*"))
            if not candidates:
                logger.warning(f"Index dosyasi bulunamadi: {self.data_root}")
                return
            index_path = candidates[0]

        logger.info(f"Index: {index_path}")

        with open(index_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                pdb_id = parts[0].lower()
                try:
                    pkd = float(parts[3])
                except (ValueError, IndexError):
                    continue

                # SDF dosyasinin varligini kontrol et
                sdf = self.data_root / pdb_id / f"{pdb_id}_ligand.sdf"
                if sdf.exists():
                    self._entries.append({"pdb_id": pdb_id, "pKd": pkd, "sdf": str(sdf)})

        logger.info(f"{len(self._entries)} kompleks yuklendi")

    def len(self) -> int:
        return len(self._entries)

    def get(self, idx: int) -> Data:
        entry = self._entries[idx]

        from rdkit import Chem
        from ml.features import smiles_to_graph

        # SDF -> SMILES -> Graph
        suppl = Chem.SDMolSupplier(entry["sdf"], removeHs=True)
        mol = next((m for m in suppl if m is not None), None)

        if mol is None:
            # Fallback: bos graf
            return Data(
                x=torch.zeros((1, 79), dtype=torch.float),
                edge_index=torch.zeros((2, 0), dtype=torch.long),
                edge_attr=torch.zeros((0, 10), dtype=torch.float),
                y=torch.tensor([entry["pKd"]], dtype=torch.float),
            )

        smiles = Chem.MolToSmiles(mol)
        graph = smiles_to_graph(smiles)
        graph.y = torch.tensor([entry["pKd"]], dtype=torch.float)
        graph.pdb_id = entry["pdb_id"]
        return graph

    @property
    def pdb_ids(self):
        return [e["pdb_id"] for e in self._entries]


def prepare_data_dir(data_dir: str):
    """Veri dizini yapisi olustur."""
    dirs = [
        "data/pdbbind",
        "data/processed",
        "data/raw",
    ]
    base = Path(data_dir).parent if "pdbbind" in data_dir else Path(data_dir)
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Veri dizinleri olusturuldu: {base}")
