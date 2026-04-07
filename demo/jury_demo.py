"""
NeoBioAI — demo/jury_demo.py
==============================
Jüri demo senaryosu — 5 ilaç adayı için binding affinity tahmini.
Sonuçları tablo formatında yazar.

Çalıştırma:
  python demo/jury_demo.py
"""

import sys
import os
import time

# Proje kökünü path'e ekle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def run_demo():
    print("=" * 70)
    print("  NEOBIOAI — Yapay Zeka Tabanlı İlaç Keşif Platformu")
    print("  Tez Demo | GINEConv GNN | PDBBind v2020")
    print("=" * 70)
    print()

    # 5 test molekülü
    molecules = [
        ("Aspirin",    "CC(=O)Oc1ccccc1C(=O)O",              "Anti-enflamatuvar (COX-2)"),
        ("5-FU",       "O=c1[nH]cc(F)c(=O)[nH]1",            "Anti-kanser (DNA sentezi)"),
        ("Ibuprofen",  "CC(C)Cc1ccc(cc1)C(C)C(=O)O",         "Anti-enflamatuvar (COX-1/2)"),
        ("Imatinib",   "Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C",
                       "Anti-lösemi (BCR-ABL kinaz)"),
        ("Caffeine",   "Cn1cnc2c1c(=O)n(c(=O)n2C)C",         "Adenozin reseptör antagonisti"),
    ]

    from backend.services.ml_service import predict_binding_affinity, get_model_info

    # Model bilgisi
    info = get_model_info()
    mode = "🤖 GNN Model" if info["loaded"] else "⚡ Mock Mod (GNN eğitilmemiş)"
    print(f"  Mod: {mode}")
    if info["loaded"]:
        print(f"  Parametre: {info['params']:,} | Device: {info['device']}")
    print()

    def affinity_label(pkd):
        if pkd is None:  return "?     "
        if pkd < 5:      return "Zayıf  "
        if pkd < 7:      return "Orta   "
        if pkd < 9:      return "Güçlü  "
        return              "⭐ ÇokGüçlü"

    # Başlık
    print(f"  {'Molekül':<14} {'pKd':>6} {'Bağlanma':>12} {'Süre(ms)':>9}  Hedef")
    print(f"  {'-'*14} {'-'*6} {'-'*12} {'-'*9}  {'-'*30}")

    total_ms = 0
    for name, smiles, target in molecules:
        result = predict_binding_affinity(smiles)
        pkd    = result["predicted_pKd"]
        ms     = result["runtime_ms"]
        total_ms += ms
        label  = affinity_label(pkd)
        pkd_str = f"{pkd:.3f}" if pkd is not None else " N/A"
        print(f"  {name:<14} {pkd_str:>6} {label:>12} {ms:>8.1f}ms  {target}")

    print()
    print(f"  Toplam tahmin süresi: {total_ms:.1f}ms | Ortalama: {total_ms/len(molecules):.1f}ms/mol")
    print()
    print("  API Endpoints:")
    print("    POST http://localhost:8000/predict  — Tekil tahmin")
    print("    POST http://localhost:8000/batch    — Toplu tahmin")
    print("    GET  http://localhost:8000/health   — Sistem durumu")
    print("    GET  http://localhost:8000/docs     — Swagger UI")
    print()
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
