"""
Neo-Dock -- ml/model_info.py
=============================
Egitilmis modelin mimari + hyperparametre + egitim metrik ozetini yazdirir.

Kullanim:
  python ml/model_info.py
"""

import sys, json
from pathlib import Path
import torch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ml.model_v2 import NeoDockGNN


def main():
    model_dir = ROOT / "ml" / "model_final"
    cfg_path  = model_dir / "config.json"
    pt_path   = model_dir / "best_model.pt"

    if not cfg_path.exists():
        print("[HATA] config.json yok — modeli egitmedin mi?")
        sys.exit(1)

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    model = NeoDockGNN(
        hidden_dim   = cfg["hidden_dim"],
        n_lig_layers = cfg["n_layers"],
        dropout      = cfg.get("dropout", 0.1),
        use_pocket   = cfg.get("use_pocket", False),
        node_dim     = cfg.get("node_dim", 79),
        edge_dim     = cfg.get("edge_dim", 10),
    )
    if pt_path.exists():
        model.load_state_dict(torch.load(pt_path, map_location="cpu", weights_only=True))

    total  = sum(p.numel() for p in model.parameters())
    train_ = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print("=" * 72)
    print("  NEO-DOCK GNN — MODEL BILGI OZETI")
    print("=" * 72)
    print(f"  Versiyon          : {cfg.get('version','v1.0')}")
    print(f"  Agirlik dosyasi   : {pt_path.name}  ({pt_path.stat().st_size/1024:.1f} KB)")
    print()
    print("  [ Mimari ]")
    print(f"    Tip              : GINEConv Graph Neural Network")
    print(f"    Hidden dim       : {cfg['hidden_dim']}")
    print(f"    GINE katmani     : {cfg['n_layers']}")
    print(f"    Dropout          : {cfg.get('dropout', 0.1)}")
    print(f"    Node (atom) dim  : {cfg.get('node_dim', 79)}")
    print(f"    Edge (bond) dim  : {cfg.get('edge_dim', 10)}")
    print(f"    Pooling          : mean + max (concat)")
    print(f"    Toplam parametre : {total:,}")
    print(f"    Egitilebilir     : {train_:,}")
    print()
    print("  [ Dataset (PDBBind) ]")
    print(f"    Train            : {cfg.get('train_size', '?')}")
    print(f"    Val              : {cfg.get('val_size', '?')}")
    print(f"    Test             : {cfg.get('test_size', '?')}")
    print()
    print("  [ Egitim sonucu ]")
    print(f"    Epochs trained   : {cfg.get('epochs_trained', '?')}")
    print(f"    Egitim suresi    : {cfg.get('train_time_seconds', '?')} s")
    print(f"    Best Val RMSE    : {cfg.get('best_val_rmse', '?')}")
    print(f"    Test RMSE        : {cfg.get('test_rmse', '?')}")
    print(f"    Test PCC         : {cfg.get('test_pcc', '?')}")
    print(f"    Test R^2         : {cfg.get('test_r2', 'N/A (yeniden egitim gerekir)')}")
    print("=" * 72)

    # Katman detayi
    print("\n  [ Katman listesi ]")
    for name, p in model.named_parameters():
        print(f"    {name:45s}  shape={tuple(p.shape)}  ({p.numel():,} param)")


if __name__ == "__main__":
    main()
