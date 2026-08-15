"""Local visualization utilities using matplotlib and pandas.

Functions here create and save plots to the web/static folder by default.
"""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parents[2] / "web" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def plot_price_series(df: pd.DataFrame, ts_col: str = "ts", price_col: str = "price", out_path: str | None = None):
    if out_path is None:
        out_path = STATIC_DIR / "price_series.png"
    else:
        out_path = Path(out_path)
    df_sorted = df.sort_values(ts_col)
    plt.figure(figsize=(10, 4))
    plt.plot(df_sorted[ts_col], df_sorted[price_col], marker=".")
    plt.title("Price series")
    plt.xlabel(ts_col)
    plt.ylabel(price_col)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return str(out_path)

if __name__ == "__main__":
    import pandas as pd
    df = pd.DataFrame({"ts": pd.date_range("2020-01-01", periods=10), "price": range(10)})
    print("Saved:", plot_price_series(df))
