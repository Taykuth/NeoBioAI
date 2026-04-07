"""
Neo-Dock — ml/train.py
========================
PDBBind veri seti ile GINEConv GNN eğitim scripti.

Kullanım:
  python ml/train.py --data_dir data/pdbbind --epochs 100

Veri akışı:
  1. PDBBind index dosyasından pKd değerlerini oku
  2. SMILES → PyG graph dönüşümü (features.py)
  3. Train/Val/Test bölme (80/10/10)
  4. GINEConv GNN eğitimi (model_v2.py)
  5. En iyi modeli kaydet (ml/model_final/)

PDBBind v2020.R1 formatı:
  - INDEX_general_PL.2020 → PDB kodları + pKd değerleri
  - {pdb_id}/{pdb_id}_ligand.sdf → ligand 3D yapısı
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

# Proje kokunu ekle
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ─── Veri Yukleme ─────────────────────────────────────────

import re
import math

# Birim carpanlari (Molar cinsinden)
UNIT_MULTIPLIERS = {
    "M": 1.0,
    "mM": 1e-3,
    "uM": 1e-6,
    "nM": 1e-9,
    "pM": 1e-12,
    "fM": 1e-15,
}


def parse_binding_value(raw: str):
    """
    PDBBind v2020.R1 formatindaki baglama verisini pKd'ye donustur.

    Ornekler:
      'Kd=49uM'      -> pKd = -log10(49e-6) = 4.31
      'Ki=0.43nM'     -> pKd = -log10(0.43e-9) = 9.37
      'IC50=1.2uM'    -> pKd = -log10(1.2e-6) = 5.92
      'Kd<10uM'       -> None (belirsiz, atla)
      'Kd>100uM'      -> None (belirsiz, atla)
      'Kd~5uM'        -> pKd = -log10(5e-6) = 5.30
    """
    # < veya > isaretlileri atla (belirsiz)
    if "<" in raw or ">" in raw:
        return None

    # ~ isareti varsa koy (yaklasik deger, kabul edilebilir)
    raw = raw.replace("~", "")

    # Kd=49uM, Ki=0.43nM, IC50=1.2uM formatini parse et
    match = re.match(r'(?:Kd|Ki|IC50|EC50|Kd1|Kd2|Ka)=([\d.]+)(\w+)', raw)
    if not match:
        return None

    value_str, unit = match.group(1), match.group(2)
    try:
        value = float(value_str)
    except ValueError:
        return None

    if value <= 0:
        return None

    multiplier = UNIT_MULTIPLIERS.get(unit)
    if multiplier is None:
        return None

    molar = value * multiplier
    if molar <= 0:
        return None

    pkd = -math.log10(molar)
    return round(pkd, 3)


def parse_pdbbind_index(index_file: str) -> dict:
    """
    PDBBind v2020.R1 INDEX dosyasini parse et.
    Format: PDB_code  resolution  year  binding_data  // ...
    Dondu: {pdb_id: {"pKd": float}}
    """
    entries = {}
    skipped_types = {}
    with open(index_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            pdb_id = parts[0].lower()
            raw_binding = parts[3]  # e.g. "Kd=49uM" or "Ki=0.43nM"

            pkd = parse_binding_value(raw_binding)
            if pkd is not None and 0 < pkd < 15:
                entries[pdb_id] = {"pKd": pkd}
            else:
                # Neden atlandi takip et
                reason = raw_binding.split("=")[0] if "=" in raw_binding else "unknown"
                skipped_types[reason] = skipped_types.get(reason, 0) + 1

    logger.info(f"Index'ten {len(entries)} kompleks yuklendi (pKd donusumu): {index_file}")
    if skipped_types:
        logger.info(f"Atlanan: {dict(skipped_types)}")
    return entries


def load_smiles_from_sdf(sdf_path: str) -> str:
    """SDF dosyasindan SMILES cikart (RDKit)."""
    from rdkit import Chem
    suppl = Chem.SDMolSupplier(str(sdf_path), removeHs=True)
    for mol in suppl:
        if mol is not None:
            return Chem.MolToSmiles(mol)
    return None


def find_ligand_sdf(data_dir: Path, pdb_id: str):
    """
    PDBBind v2020.R1 dizin yapisinda ligand SDF dosyasini bul.
    Desteklenen yapilar:
      - data_dir/{pdb_id}/{pdb_id}_ligand.sdf  (duz yapi)
      - data_dir/{yil_aralik}/{pdb_id}/{pdb_id}_ligand.sdf  (2001-2010/1cs4/...)
    """
    # Direkt yol
    direct = data_dir / pdb_id / f"{pdb_id}_ligand.sdf"
    if direct.exists():
        return direct
    direct_mol2 = data_dir / pdb_id / f"{pdb_id}_ligand.mol2"
    if direct_mol2.exists():
        return direct_mol2

    # Yil-bazli alt dizin yapisi (1981-2000, 2001-2010, 2011-2019)
    for subdir in data_dir.iterdir():
        if subdir.is_dir() and '-' in subdir.name:
            sdf = subdir / pdb_id / f"{pdb_id}_ligand.sdf"
            if sdf.exists():
                return sdf
            mol2 = subdir / pdb_id / f"{pdb_id}_ligand.mol2"
            if mol2.exists():
                return mol2
    return None


def build_dataset(data_dir: str, index_entries: dict, max_samples: int = 0) -> list:
    """
    PDBBind dizininden PyG Data listesi olustur.
    Her entry: Data(x, edge_index, edge_attr, y=pkd)
    max_samples=0 ise tum verileri yukle.
    """
    from ml.features import smiles_to_graph

    dataset = []
    skipped = 0
    data_path = Path(data_dir)
    total = len(index_entries)

    for i, (pdb_id, info) in enumerate(index_entries.items()):
        if max_samples > 0 and len(dataset) >= max_samples:
            break

        if (i + 1) % 500 == 0:
            logger.info(f"  Isleniyor: {i+1}/{total} ({len(dataset)} basarili)")

        sdf_file = find_ligand_sdf(data_path, pdb_id)
        if sdf_file is None:
            skipped += 1
            continue

        try:
            smiles = load_smiles_from_sdf(str(sdf_file))
            if smiles is None:
                skipped += 1
                continue

            graph = smiles_to_graph(smiles)
            graph.y = torch.tensor([info["pKd"]], dtype=torch.float)
            graph.pdb_id = pdb_id
            dataset.append(graph)
        except Exception as e:
            skipped += 1
            continue

    logger.info(f"Dataset: {len(dataset)} basarili | {skipped} atlandi")
    return dataset


def split_dataset(dataset: list, train_ratio=0.8, val_ratio=0.1, seed=42):
    """Train/Val/Test bolme."""
    np.random.seed(seed)
    indices = np.random.permutation(len(dataset))

    n_train = int(len(dataset) * train_ratio)
    n_val = int(len(dataset) * val_ratio)

    train_idx = indices[:n_train]
    val_idx = indices[n_train:n_train + n_val]
    test_idx = indices[n_train + n_val:]

    train = [dataset[i] for i in train_idx]
    val = [dataset[i] for i in val_idx]
    test = [dataset[i] for i in test_idx]

    logger.info(f"Split: Train={len(train)} | Val={len(val)} | Test={len(test)}")
    return train, val, test


# ─── Egitim Dongusu ───────────────────────────────────────

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    n = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        pred = model(batch).squeeze(-1)
        loss = criterion(pred, batch.y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
        n += batch.num_graphs
    return total_loss / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    preds, targets = [], []
    for batch in loader:
        batch = batch.to(device)
        pred = model(batch).squeeze(-1)
        preds.append(pred.cpu().numpy())
        targets.append(batch.y.cpu().numpy())

    preds = np.concatenate(preds)
    targets = np.concatenate(targets)

    rmse = np.sqrt(np.mean((preds - targets) ** 2))

    # Pearson correlation
    if len(preds) > 1:
        pcc = np.corrcoef(preds, targets)[0, 1]
    else:
        pcc = 0.0

    return {"rmse": round(rmse, 4), "pcc": round(pcc, 4), "n": len(preds)}


# ─── Ana Fonksiyon ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Neo-Dock GNN Egitim")
    parser.add_argument("--data_dir", type=str, default="data/pdbbind",
                        help="PDBBind veri dizini")
    parser.add_argument("--index_file", type=str, default=None,
                        help="PDBBind index dosyasi (None=otomatik bul)")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--hidden_dim", type=int, default=128)
    parser.add_argument("--n_layers", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=15,
                        help="Early stopping patience")
    parser.add_argument("--output_dir", type=str, default="ml/model_final")
    parser.add_argument("--max_samples", type=int, default=0,
                        help="Maks ornek sayisi (0=tumu)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    # ── Index dosyasini bul ──────────────────────────────
    if args.index_file:
        index_file = args.index_file
    else:
        # Otomatik arama
        candidates = [
            Path(args.data_dir) / "INDEX_general_PL.2020",
            Path(args.data_dir) / "INDEX_general_PL_data.2020",
            Path(args.data_dir) / "index" / "INDEX_general_PL.2020",
            Path(args.data_dir) / "INDEX_general_PL_data.2016",
        ]
        index_file = None
        for c in candidates:
            if c.exists():
                index_file = str(c)
                break
        if index_file is None:
            # Glob ile bul
            found = list(Path(args.data_dir).rglob("INDEX_*PL*"))
            if found:
                index_file = str(found[0])
            else:
                logger.error(f"Index dosyasi bulunamadi: {args.data_dir}")
                logger.error("Beklenen: INDEX_general_PL.2020 veya INDEX_general_PL_data.2020")
                sys.exit(1)

    logger.info(f"Index dosyasi: {index_file}")

    # ── Dataset yukle ────────────────────────────────────
    entries = parse_pdbbind_index(index_file)
    dataset = build_dataset(args.data_dir, entries, max_samples=args.max_samples)

    if len(dataset) < 10:
        logger.error(f"Yeterli veri yok ({len(dataset)} graf). "
                     f"data_dir icinde {{pdb_id}}/{{pdb_id}}_ligand.sdf dosyalari var mi?")
        sys.exit(1)

    train_data, val_data, test_data = split_dataset(dataset)

    # ── DataLoader ───────────────────────────────────────
    from torch_geometric.loader import DataLoader

    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=args.batch_size)
    test_loader = DataLoader(test_data, batch_size=args.batch_size)

    # ── Model ────────────────────────────────────────────
    from ml.model_v2 import NeoDockGNN

    # Otomatik boyut tespiti
    sample = dataset[0]
    node_dim = sample.x.shape[1]
    edge_dim = sample.edge_attr.shape[1] if sample.edge_attr is not None else 10

    model = NeoDockGNN(
        hidden_dim=args.hidden_dim,
        n_lig_layers=args.n_layers,
        dropout=args.dropout,
        node_dim=node_dim,
        edge_dim=edge_dim,
    ).to(device)

    logger.info(f"Model: {model.count_parameters():,} parametre | "
                f"hidden={args.hidden_dim} | layers={args.n_layers}")

    optimizer = Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5,
                                  patience=7, min_lr=1e-6)
    criterion = nn.MSELoss()

    # ── Egitim ───────────────────────────────────────────
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    best_val_rmse = float("inf")
    patience_counter = 0
    history = []

    logger.info(f"Egitim basliyor: {args.epochs} epoch | batch={args.batch_size}")
    t_start = time.time()

    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_metrics = evaluate(model, val_loader, device)
        scheduler.step(val_metrics["rmse"])

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            **val_metrics,
        })

        current_lr = optimizer.param_groups[0]["lr"]

        if epoch % 5 == 0 or epoch == 1:
            logger.info(
                f"Epoch {epoch:3d}/{args.epochs} | "
                f"Loss={train_loss:.4f} | "
                f"Val RMSE={val_metrics['rmse']:.4f} | "
                f"Val PCC={val_metrics['pcc']:.4f} | "
                f"LR={current_lr:.1e}"
            )

        # En iyi modeli kaydet
        if val_metrics["rmse"] < best_val_rmse:
            best_val_rmse = val_metrics["rmse"]
            patience_counter = 0
            torch.save(model.state_dict(), output_dir / "best_model.pt")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                logger.info(f"Early stopping: {args.patience} epoch iyilesme yok")
                break

    train_time = time.time() - t_start
    logger.info(f"Egitim tamamlandi: {train_time:.1f}s ({train_time/60:.1f} dk)")

    # ── Test seti degerlendirme ──────────────────────────
    model.load_state_dict(torch.load(output_dir / "best_model.pt", weights_only=True))
    test_metrics = evaluate(model, test_loader, device)
    logger.info(f"TEST | RMSE={test_metrics['rmse']:.4f} | PCC={test_metrics['pcc']:.4f} | N={test_metrics['n']}")

    # ── Config + sonuclari kaydet ────────────────────────
    config = {
        "version": "v1.0",
        "hidden_dim": args.hidden_dim,
        "n_layers": args.n_layers,
        "dropout": args.dropout,
        "use_pocket": False,
        "node_dim": node_dim,
        "edge_dim": edge_dim,
        "train_size": len(train_data),
        "val_size": len(val_data),
        "test_size": len(test_data),
        "best_val_rmse": float(best_val_rmse),
        "test_rmse": float(test_metrics["rmse"]),
        "test_pcc": float(test_metrics["pcc"]),
        "epochs_trained": len(history),
        "train_time_seconds": round(train_time, 1),
    }

    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2, default=lambda o: float(o) if hasattr(o, 'item') else str(o))

    # History'deki numpy float'lari da temizle
    clean_history = []
    for h in history:
        clean_history.append({k: float(v) if hasattr(v, 'item') else v for k, v in h.items()})

    with open(output_dir / "history.json", "w") as f:
        json.dump(clean_history, f, indent=2)

    logger.info(f"Kaydedildi: {output_dir}/best_model.pt + config.json")
    logger.info("Model artik mock mod yerine gercek tahmin yapar!")


if __name__ == "__main__":
    main()
