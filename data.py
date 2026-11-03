"""Get Statistics Canada table 36-10-0104 and build the five national accounts series."""
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "36100104-eng.zip"
OUTPUT, FIGURES = ROOT / "output", ROOT / "figures"
URL = "https://www150.statcan.gc.ca/n1/tbl/csv/36100104-eng.zip"

GDP = "Gross domestic product at market prices"
FINAL = "Final consumption expenditure"
DURABLES = "Durable goods"
GOV_C = "General governments final consumption expenditure"
GFCF = "Gross fixed capital formation"
GOV_I = "General governments gross fixed capital formation"
INVENTORIES = "Investment in inventories"
EXPORTS = "Exports of goods and services"
IMPORTS = "Less: imports of goods and services"

# Quarterly peak and trough from the C.D. Howe Institute Business Cycle Council's 2021 chronology:
# https://cdhowe.org/wp-content/uploads/2024/06/Recession_Chronology_0.xlsx
# The 1960-61 recession ends in the first quarter of the data, so it is left out.
RECESSIONS = {"1974-75": ("1974Q3", "1975Q1"), "1981-82": ("1981Q2", "1982Q4"), "1990-92": ("1990Q1", "1992Q2"),
              "2008-09": ("2008Q3", "2009Q2"), "2020": ("2019Q4", "2020Q2")}


def download():
    RAW.parent.mkdir(exist_ok=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=300) as r:
        RAW.write_bytes(r.read())


def read_table(path=RAW):
    """Quarterly, chained dollars, seasonally adjusted at annual rates, in millions. One column per line of the table."""
    with zipfile.ZipFile(path) as z, z.open("36100104.csv") as f:
        d = pd.read_csv(f, dtype={"VALUE": float})
    # Older chained bases stay in the file marked as terminated, so this follows a rebasing without a code change.
    keep = d.Prices.str.fullmatch(r"Chained \(\d{4}\) dollars") & d.TERMINATED.isna() \
        & (d["Seasonal adjustment"] == "Seasonally adjusted at annual rates")
    d = d[keep]
    if d.Prices.nunique() != 1:
        raise ValueError(f"expected one chained base, found {d.Prices.unique()}")
    table = d.pivot(index="REF_DATE", columns="Estimates", values="VALUE")
    table.index = pd.PeriodIndex(table.index, freq="Q")
    return table


def components(table):
    """Output and its parts. Chained series do not add up exactly, so these are approximations by subtraction."""
    parts = pd.DataFrame({"Y": table[GDP],
                          "C": table[FINAL] - table[DURABLES] - table[GOV_C],
                          "I": table[GFCF] + table[DURABLES] + table[INVENTORIES] - table[GOV_I],
                          "G": table[GOV_C] + table[GOV_I],
                          "NX": table[EXPORTS] - table[IMPORTS]})
    if parts.isna().any().any():
        raise ValueError("a series has missing quarters")
    return parts


if __name__ == "__main__":
    download()
    print(read_table().index[[0, -1]])
