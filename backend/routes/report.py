"""
Neo-Dock -- backend/routes/report.py
=====================================
POST /report -- SMILES tahmini + explainability + insan-okur rapor.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.ml_service     import predict_binding_affinity
from backend.services.explain_service import explain
from backend.services.llm_service     import generate_report

router = APIRouter(tags=["report"])


def _affinity_label(pkd: float) -> str:
    if pkd < 5:  return "weak"
    if pkd < 7:  return "moderate"
    if pkd < 9:  return "strong"
    return "very_strong"


class ReportRequest(BaseModel):
    smiles:        str  = Field(..., example="CC(=O)Oc1ccccc1C(=O)O")
    explain:       bool = True
    force_local:   bool = False   # True -> OpenAI'yi atla, sablon kullan


@router.post("/report", summary="Tahmin + explain + LLM rapor")
def report_route(req: ReportRequest):
    pred = predict_binding_affinity(req.smiles.strip())
    if pred.get("predicted_pKd") is None:
        raise HTTPException(status_code=422, detail=pred.get("error", "Tahmin yapilamadi"))

    pkd   = pred["predicted_pKd"]
    label = _affinity_label(pkd)

    top_atoms = None
    explain_block = None
    if req.explain:
        ex = explain(req.smiles.strip(), steps=20, top_k=8)
        if "error" not in ex:
            top_atoms = ex["top_atoms"]
            explain_block = ex

    report = generate_report(req.smiles.strip(), pkd, label, top_atoms,
                             force_local=req.force_local)

    return {
        "smiles":         req.smiles,
        "predicted_pKd":  pkd,
        "affinity_label": label,
        "runtime_ms":     pred.get("runtime_ms"),
        "model_version":  pred.get("model_version"),
        "explain":        explain_block,
        "report":         report["report"],
        "report_backend": report["backend"],
        "report_model":   report["model"],
    }
