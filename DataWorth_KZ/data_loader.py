"""DataWorth KZ — data loader.

Loads the UCI "Default of Credit Card Clients" dataset (Yeh & Lien, 2009; Taiwan, Apr–Sep 2005).
IMPORTANT: these are historical Taiwanese credit-card data, NOT Kazakhstani Open Banking data.

Sources (tried in order):
  1. local file data/UCI_Credit_Card.csv (Kaggle/UCI CSV layout)
  2. local file data/default of credit card clients.xls (original UCI layout, header on row 2)
  3. official UCI archive (https://archive.ics.uci.edu/dataset/350)
  4. public GitHub mirror of the CSV (integrity checked against known statistics below)
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
UCI_ZIP = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
MIRROR_CSV = ("https://raw.githubusercontent.com/gdmarmerola/random-stuff/master/"
              "probability_calibration/UCI_Credit_Card.csv")
TARGET = "DEFAULT"

PAY_STATUS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
PAY_AMT = [f"PAY_AMT{i}" for i in range(1, 7)]
DEMOGRAPHIC = ["SEX", "EDUCATION", "MARRIAGE", "AGE"]

FEATURE_SETS = {
    "A": ["LIMIT_BAL", "PAY_0"],
    "B": ["LIMIT_BAL", "PAY_0", "PAY_2", "PAY_3", "BILL_AMT1", "PAY_AMT1"],
    "C": ["LIMIT_BAL"] + PAY_STATUS + BILL + PAY_AMT,
}

# Published reference statistics of the original UCI file, used as an integrity check.
REFERENCE = {"n_rows": 30000, "n_default": 6636, "limit_bal_mean": 167484.32}


def _standardise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={"default.payment.next.month": TARGET,
                            "default payment next month": TARGET,
                            "PAY_1": "PAY_0"})
    df.columns = [c.strip() for c in df.columns]
    return df


def _from_uci_zip() -> pd.DataFrame:
    import urllib.request
    raw = urllib.request.urlopen(UCI_ZIP, timeout=30).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = [n for n in z.namelist() if n.endswith(".xls")][0]
        return pd.read_excel(z.open(name), header=1)


def load_raw() -> pd.DataFrame:
    csv = DATA_DIR / "UCI_Credit_Card.csv"
    xls = DATA_DIR / "default of credit card clients.xls"
    if csv.exists():
        df = pd.read_csv(csv)
    elif xls.exists():
        df = pd.read_excel(xls, header=1)
    else:
        try:
            df = _from_uci_zip()
        except Exception:
            df = pd.read_csv(MIRROR_CSV)
        DATA_DIR.mkdir(exist_ok=True)
        _standardise(df).to_csv(csv, index=False)
    return _standardise(df)


def integrity_check(df: pd.DataFrame) -> dict:
    res = {
        "n_rows": len(df),
        "n_default": int(df[TARGET].sum()),
        "limit_bal_mean": round(float(df["LIMIT_BAL"].mean()), 2),
    }
    res["matches_reference"] = (res["n_rows"] == REFERENCE["n_rows"]
                                and res["n_default"] == REFERENCE["n_default"]
                                and abs(res["limit_bal_mean"] - REFERENCE["limit_bal_mean"]) < 0.01)
    return res


def load() -> pd.DataFrame:
    df = load_raw()
    chk = integrity_check(df)
    if not chk["matches_reference"]:
        raise ValueError(f"Dataset does not match UCI reference statistics: {chk}")
    return df


if __name__ == "__main__":
    d = load()
    print(d.shape, integrity_check(d))
