"""
Neo-Dock -- backend/routes/explain.py
======================================
POST /explain -- atom-seviye Integrated Gradients explainability.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.services.explain_service import explain

router = APIRouter(tags=["explain"])


class ExplainRequest(BaseModel):
    smiles: str = Field(..., example="CC(=O)Oc1ccccc1C(=O)O")
    steps:  int = Field(20, ge=5, le=100)
    top_k:  int = Field(8, ge=1, le=30)


@router.post("/explain", summary="Atom-seviye katki analizi")
def explain_route(req: ExplainRequest):
    result = explain(req.smiles.strip(), steps=req.steps, top_k=req.top_k)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result
