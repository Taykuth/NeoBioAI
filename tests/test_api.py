"""
NeoBioAI — tests/test_api.py
==============================
Backend API entegrasyon testleri.

Calistirma:
  python tests/test_api.py
  (Backend localhost:8000'de calisiyor olmali)
"""

import sys
import json
import requests

API = "http://localhost:8000"
PASS = 0
FAIL = 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -- {detail}")


def main():
    print("=" * 60)
    print("  NEOBIOAI API Test Suite")
    print("=" * 60)
    print()

    # ── 1. Root ──────────────────────────────────────────
    print("--- Root ---")
    try:
        r = requests.get(f"{API}/", timeout=5)
        test("GET / status=200", r.status_code == 200)
        test("Root has name", data.get("name") == "NeoBioAI API")
    except Exception as e:
        test("GET / connection", False, str(e))

    # ── 2. Health ────────────────────────────────────────
    print("\n--- Health ---")
    try:
        r = requests.get(f"{API}/health", timeout=5)
        test("GET /health status=200", r.status_code == 200)
        data = r.json()
        test("Health status=ok", data.get("status") == "ok")
        test("Health has model info", "model" in data)
    except Exception as e:
        test("GET /health", False, str(e))

    # ── 3. Auth Register ─────────────────────────────────
    print("\n--- Auth ---")
    try:
        r = requests.post(f"{API}/auth/register", json={
            "email": "test_user@neodock.dev",
            "password": "testpass1234"
        }, timeout=5)
        # 200 veya 409 (zaten var) kabul edilebilir
        test("POST /auth/register", r.status_code in [200, 409])
    except Exception as e:
        test("POST /auth/register", False, str(e))

    # ── 4. Auth Login ────────────────────────────────────
    token = None
    try:
        r = requests.post(f"{API}/auth/login", json={
            "email": "demo@neodock.dev",
            "password": "demo1234"
        }, timeout=5)
        test("POST /auth/login status=200", r.status_code == 200)
        data = r.json()
        token = data.get("access_token")
        test("Login returns token", token is not None and len(token) > 20)
        test("Login token_type=Bearer", data.get("token_type") == "Bearer")
    except Exception as e:
        test("POST /auth/login", False, str(e))

    # ── 5. Auth Me ───────────────────────────────────────
    if token:
        try:
            r = requests.get(f"{API}/auth/me", headers={
                "Authorization": f"Bearer {token}"
            }, timeout=5)
            test("GET /auth/me status=200", r.status_code == 200)
            data = r.json()
            test("Me returns email", data.get("email") == "demo@neodock.dev")
            test("Me returns tier", data.get("tier") in ["free", "pro"])
        except Exception as e:
            test("GET /auth/me", False, str(e))

    # ── 6. Predict (guest) ───────────────────────────────
    print("\n--- Predict ---")
    try:
        r = requests.post(f"{API}/predict", json={
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",
            "mode": "fast"
        }, timeout=10)
        test("POST /predict status=200", r.status_code == 200)
        data = r.json()
        test("Predict has pKd", data.get("predicted_pKd") is not None)
        test("Predict pKd > 0", (data.get("predicted_pKd") or 0) > 0)
        test("Predict has runtime", "runtime_ms" in data)
        test("Predict has affinity_label", "affinity_label" in data)
        test("Predict user_tier=guest", data.get("user_tier") == "guest")
    except Exception as e:
        test("POST /predict", False, str(e))

    # ── 7. Predict (invalid SMILES) ──────────────────────
    try:
        r = requests.post(f"{API}/predict", json={
            "smiles": "INVALID_XYZ",
            "mode": "fast"
        }, timeout=10)
        # Mock mod'da invalid SMILES bile calisir (hash'den deger uretir)
        test("POST /predict invalid SMILES", r.status_code in [200, 422])
    except Exception as e:
        test("POST /predict invalid", False, str(e))

    # ── 8. Predict (auth) ────────────────────────────────
    if token:
        try:
            r = requests.post(f"{API}/predict", json={
                "smiles": "O=c1[nH]cc(F)c(=O)[nH]1",
                "mode": "fast"
            }, headers={"Authorization": f"Bearer {token}"}, timeout=10)
            test("POST /predict with auth", r.status_code == 200)
            data = r.json()
            test("Auth predict user_tier=pro", data.get("user_tier") == "pro")
        except Exception as e:
            test("POST /predict auth", False, str(e))

    # ── 9. Rate limit header ─────────────────────────────
    print("\n--- Middleware ---")
    try:
        r = requests.post(f"{API}/predict", json={"smiles": "C", "mode": "fast"}, timeout=5)
        test("Rate limit not triggered", r.status_code != 429)
    except Exception as e:
        test("Rate limit", False, str(e))

    # ── 10. 401 without token ────────────────────────────
    try:
        r = requests.post(f"{API}/batch", json={"smiles_list": ["C"]}, timeout=5)
        test("POST /batch without auth -> 401", r.status_code == 401)
    except Exception as e:
        test("POST /batch 401", False, str(e))

    # ── Sonuc ────────────────────────────────────────────
    print()
    print("=" * 60)
    total = PASS + FAIL
    print(f"  Sonuc: {PASS}/{total} test basarili")
    if FAIL > 0:
        print(f"  {FAIL} test BASARISIZ")
    else:
        print("  Tum testler basarili!")
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
