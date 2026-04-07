"""
Neo-Dock — backend/routes/predict.py
=====================================
POST /predict — SMILES → pKd binding affinity tahmini
POST /batch   — Toplu tahmin
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.auth_jwt.auth import get_current_user, optional_user, User
from backend.services.ml_service import predict_binding_affinity, batch_predict

router = APIRouter(tags=["predict"])


class PredictRequest(BaseModel):
    smiles: str       = Field(..., example="CC(=O)Oc1ccccc1C(=O)O",
                              description="Molecular SMILES string")
    pdb_id: Optional[str] = Field(None, example="1HEW",
                                   description="Protein PDB ID (opsiyonel)")
    mode:   str       = Field("fast", description="fast | detailed")

    class Config:
        json_schema_extra = {
            "example": {
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "pdb_id": None,
                "mode":   "fast",
            }
        }


class BatchRequest(BaseModel):
    smiles_list: list[str] = Field(..., min_length=1, max_length=100)


def _affinity_label(pkd: float) -> str:
    if pkd < 5:    return "weak"
    if pkd < 7:    return "moderate"
    if pkd < 9:    return "strong"
    return "very_strong"


@router.post("/predict", summary="SMILES → pKd tahmini")
def predict(
    req:  PredictRequest,
    user: Optional[User] = Depends(optional_user),
):
    """
    Verilen SMILES için protein-ligand bağlanma afinitesi (pKd) tahmin eder.

    pKd yorumu:
    - < 5   → Zayıf bağlanma
    - 5–7   → Orta bağlanma
    - 7–9   → Güçlü (ilaç adayı)
    - > 9   → Çok güçlü (umut verici aday)
    """
    if not req.smiles or len(req.smiles.strip()) < 2:
        raise HTTPException(status_code=422, detail="Geçerli bir SMILES girin")

    result = predict_binding_affinity(req.smiles.strip(), req.pdb_id)

    if result.get("error") and result.get("predicted_pKd") is None:
        raise HTTPException(status_code=422, detail=result["error"])

    pkd = result.get("predicted_pKd")

    return {
        **result,
        "smiles":         req.smiles,
        "affinity_label": _affinity_label(pkd) if pkd is not None else "unknown",
        "user_tier":      user.tier if user else "guest",
    }


@router.post("/batch", summary="Toplu SMILES tahmini", dependencies=[Depends(get_current_user)])
def batch(req: BatchRequest):
    """
    Birden fazla molekül için toplu tahmin (auth gerekli, max 100 SMILES).
    """
    results = batch_predict(req.smiles_list)
    return {
        "count":   len(results),
        "results": [
            {**r, "affinity_label": _affinity_label(r["predicted_pKd"])
             if r.get("predicted_pKd") is not None else "unknown"}
            for r in results
        ],
    }
