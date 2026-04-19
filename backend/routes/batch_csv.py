"""
Neo-Dock -- backend/routes/batch_csv.py
========================================
POST /batch_csv  -- CSV dosyasi yukle, her satir icin SMILES tahmin et, CSV dondur.

CSV formati (tek kolon veya 'smiles' ba$llikli):
  smiles
  CC(=O)Oc1ccccc1C(=O)O
  CN1C=NC2=C1C(=O)N(C(=O)N2C)C
"""

from io import StringIO
import csv
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.ml_service import predict_binding_affinity

router = APIRouter(tags=["batch"])


def _label(pkd):
    if pkd is None:   return "unknown"
    if pkd < 5:       return "weak"
    if pkd < 7:       return "moderate"
    if pkd < 9:       return "strong"
    return "very_strong"


@router.post("/batch_csv", summary="CSV dosyasi -> tahmin CSV")
async def batch_csv(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith((".csv", ".txt")):
        raise HTTPException(422, "CSV veya TXT dosyasi bekleniyor")

    raw = (await file.read()).decode("utf-8", errors="ignore").strip()
    if not raw:
        raise HTTPException(422, "Bos dosya")

    # Basit CSV parse (ilk kolon SMILES)
    reader = csv.reader(StringIO(raw))
    rows = [r for r in reader if r]
    if not rows:
        raise HTTPException(422, "Geçerli satır yok")

    # Başlık satırı var mı?
    first = [c.strip().lower() for c in rows[0]]
    has_header = "smiles" in first
    smiles_col = first.index("smiles") if has_header else 0
    data_rows  = rows[1:] if has_header else rows

    # Max 500 satır
    if len(data_rows) > 500:
        raise HTTPException(422, f"Max 500 satir (gelen: {len(data_rows)})")

    # Tahmin + CSV cikti
    out = StringIO()
    w = csv.writer(out)
    w.writerow(["smiles", "predicted_pKd", "affinity_label", "runtime_ms", "error"])

    ok, fail = 0, 0
    for r in data_rows:
        if len(r) <= smiles_col:
            continue
        s = r[smiles_col].strip()
        if not s:
            continue
        res = predict_binding_affinity(s)
        pkd = res.get("predicted_pKd")
        err = res.get("error") or ""
        w.writerow([
            s,
            f"{pkd:.3f}" if pkd is not None else "",
            _label(pkd),
            f"{res.get('runtime_ms', 0):.1f}",
            err,
        ])
        if pkd is not None:
            ok += 1
        else:
            fail += 1

    out.seek(0)
    fname = (file.filename or "batch").rsplit(".", 1)[0] + "_predictions.csv"
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
            "X-Neo-Success": str(ok),
            "X-Neo-Failed":  str(fail),
        },
    )
