"""
Neo-Dock -- backend/services/llm_service.py
============================================
pKd tahminini insan-okur rapora cevirir.

Oncelik:
  1) OPENAI_API_KEY var ise -> gpt-4o-mini ile rapor uretir
  2) Yoksa -> kural-tabanli Turkce sablon raporu uretir (daima calisir)
"""

import os
from typing import Optional

REPORT_SYSTEM_PROMPT = """Sen bir bioinformatik asistanisin. Kullaniciya protein-ligand baglanma afinitesi
tahminini Turkce, anlasilir, profesyonel bir tiple acikla. Format:
  - Molekul ozeti (1-2 cumle)
  - pKd yorumu (zayif/orta/guclu/cok guclu)
  - Ilac adayi olarak potansiyeli
  - Varsa explainability (onemli atomlar)
  - Onerilen bir sonraki adim
200 kelimeyi asma."""


def _rule_based_report(smiles: str, pkd: float, label: str,
                       top_atoms: Optional[list] = None) -> str:
    """Kurumsal tonlu sablon rapor. LLM yoksa da caligsin."""
    # pKd yorumu
    if pkd is None:
        yorum = "Tahmin yapilamadi."
    elif pkd < 5:
        yorum = (f"pKd ~{pkd:.2f} degeri **zayif baglanma** anlamina gelir (Kd >~ 10 uM). "
                 "Molekul muhtemelen ilac adayi olarak yetersizdir.")
    elif pkd < 7:
        yorum = (f"pKd ~{pkd:.2f} **orta seviye** baglanma. Kd mikromolar araliktadir. "
                 "Optimizasyonla gelistirilebilir.")
    elif pkd < 9:
        yorum = (f"pKd ~{pkd:.2f} **gurcu baglanma** (nanomolar Kd). "
                 "Ilac adayi olarak umut vericidir.")
    else:
        yorum = (f"pKd ~{pkd:.2f} **cok gurcu baglanma** (sub-nM). "
                 "Yuksek verimlilik potansiyeli; sectivity kontrol edilmeli.")

    atom_str = ""
    if top_atoms:
        top3 = top_atoms[:3]
        items = [f"{a['symbol']} (idx {a['atom_idx']}, {a['direction']})" for a in top3]
        atom_str = f"\n\n**En etkili atomlar (GNN a gore):** {', '.join(items)}."

    rapor = f"""**Molekul:** `{smiles}`

**Tahmin:** pKd = {pkd:.3f}  ({label})

**Yorum:** {yorum}{atom_str}

**Onerilen sonraki adim:**
- Eger pKd < 7 ise: R-group enumeration veya bio-isostere ile optimize et.
- Eger pKd >= 7 ise: ADMET profili (logP, solubility, clearance) kontrol et,
  ayni zamanda hedef proteinin kristal yapisi (PDB) ile docking skoru ile karsilastir.
"""
    return rapor.strip()


def _openai_report(smiles: str, pkd: float, label: str,
                   top_atoms: Optional[list] = None) -> str:
    """OpenAI ile rapor. Basarisiz olursa sablona duser."""
    try:
        from openai import OpenAI
    except Exception:
        return _rule_based_report(smiles, pkd, label, top_atoms)

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return _rule_based_report(smiles, pkd, label, top_atoms)

    user_prompt = (
        f"SMILES: {smiles}\n"
        f"Tahmin pKd: {pkd:.3f}  ({label})\n"
    )
    if top_atoms:
        user_prompt += "Onemli atomlar: " + ", ".join(
            f"{a['symbol']}(idx={a['atom_idx']}, contrib={a['contribution']:+.3f})"
            for a in top_atoms[:5]
        )

    try:
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return (_rule_based_report(smiles, pkd, label, top_atoms)
                + f"\n\n*(LLM hatasi, sablona dusuldu: {e})*")


def generate_report(smiles: str, pkd: float, label: str,
                    top_atoms: Optional[list] = None,
                    force_local: bool = False) -> dict:
    """Ana fonksiyon. dict doner: {report, backend, model}."""
    if force_local or not os.environ.get("OPENAI_API_KEY"):
        return {
            "report":  _rule_based_report(smiles, pkd, label, top_atoms),
            "backend": "rule_based",
            "model":   "neodock-template-v1",
        }
    text = _openai_report(smiles, pkd, label, top_atoms)
    return {"report": text, "backend": "openai", "model": "gpt-4o-mini"}
