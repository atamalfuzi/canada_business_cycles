"""Filter the series and write every table the README quotes to output/."""
import numpy as np
import pandas as pd

from data import INVENTORIES, OUTPUT, RECESSIONS, components, read_table
from filters import baxter_king, hamilton, hodrick_prescott, trend_shares

FILTERS = {"Baxter-King": baxter_king, "Hamilton": hamilton, "Hodrick-Prescott": hodrick_prescott}
SERIES = {"Y": "Output", "C": "Consumption", "I": "Investment", "G": "Government purchases"}
LAST_NORMAL = "2019Q4"  # the last quarter before the pandemic
PANDEMIC = ("2020Q1", "2021Q3")  # output was back above its 2019Q4 level in 2021Q3; the line runs on to 2021Q4


def cycles(levels):
    """One frame per filter, of log Y, C, I and G with the cycle taken out."""
    logs = np.log(levels[list(SERIES)])
    return {name: logs.apply(f) for name, f in FILTERS.items()}


def volatility(cycle, end=None):
    """Standard deviation and correlation with output of each series, over the quarters where the filter has values."""
    d = cycle.dropna()[:end]
    return pd.DataFrame({"sd": d.std(), "corr_output": d.corrwith(d.Y), "relative_sd": d.std() / d.Y.std(),
                         "first": str(d.index[0]), "last": str(d.index[-1]), "quarters": len(d)})


def volatility_table(found):
    frames = [volatility(c, end).assign(filter=name, sample=sample).rename_axis("series").reset_index()
              for name, c in found.items() for sample, end in (("all", None), ("to 2019", LAST_NORMAL))]
    return pd.concat(frames)[["filter", "sample", "series", "sd", "relative_sd", "corr_output", "first", "last", "quarters"]]


def recession_table(levels, found):
    """The fall in log output over each dated recession, and each filter's output gap at the peak and its low nearby."""
    y = np.log(levels.Y)
    rows = []
    for name, (peak, trough) in RECESSIONS.items():
        row = {"recession": name, "peak": peak, "trough": trough, "fall": y[trough] - y[peak]}
        for f, c in found.items():
            near = c.Y[pd.Period(peak) - 4:pd.Period(trough) + 4]
            row |= {f"{f} at peak": c.Y[peak], f"{f} low": near.min(), f"{f} low quarter": str(near.idxmin()),
                    f"{f} quarters to recover": quarters_below(c.Y, near.idxmin())}
        rows.append(row)
    return pd.DataFrame(rows)


def quarters_below(gap, start):
    """Quarters from the low until the gap is back at zero."""
    after = gap[start:].dropna()
    above = after[after >= 0]
    return np.nan if above.empty else (above.index[0] - start).n


def smooth_pandemic(log_output):
    """Log output with the pandemic quarters replaced by a straight line, as a series with no sudden fall."""
    out = log_output.copy()
    out[PANDEMIC[0]:PANDEMIC[1]] = np.nan
    return out.interpolate()


def leakage(levels):
    """How much the pandemic moves each filter's gap, by quarter: the gap on actual output less the gap on the smoothed series."""
    y = np.log(levels.Y)
    flat = smooth_pandemic(y)
    return pd.DataFrame({name: f(y) - f(flat) for name, f in FILTERS.items()})


def leakage_summary(leak):
    """The largest change outside the pandemic quarters, before they begin and after they end."""
    before, after = leak[:pd.Period(PANDEMIC[0]) - 1], leak[pd.Period(PANDEMIC[1]) + 1:]
    rows = []
    for name in leak:
        early, late = before[name].abs().idxmax(), after[name].abs().idxmax()
        rows.append({"filter": name, "largest before": before[name][early], "quarter before": str(early),
                     "largest after": after[name][late], "quarter after": str(late)})
    return pd.DataFrame(rows)


def real_time(y, f, start="1985Q1"):
    """The gap at each quarter as seen with data only up to then. Revised data are not undone, so this is the filter's revision only."""
    return pd.Series({t: f(y[:t]).iloc[-1] for t in y[start:].index})


def revisions(levels):
    y = np.log(levels.Y)
    rows = []
    for name in ("Hamilton", "Hodrick-Prescott"):
        f = FILTERS[name]
        seen, final = real_time(y, f), f(y)["1985Q1":]
        for sample, end in (("all", None), ("to 2019", LAST_NORMAL)):
            s, g = seen[:end], final[:end]
            rows.append({"filter": name, "sample": sample, "rms_revision": np.sqrt(((s - g) ** 2).mean()), "corr_final": s.corr(g),
                         "wrong_sign": (np.sign(s) != np.sign(g)).mean(), "sd_final": g.std(), "quarters": len(s)})
    return pd.DataFrame(rows)


def block_interval(a, b, block=16, draws=4000, seed=0):
    """95% range for the correlation of a and b, resampling circular blocks since filtered series are strongly autocorrelated."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)
    starts = rng.integers(0, n, size=(draws, n // block + 1))
    picks = (starts[:, :, None] + np.arange(block)).reshape(draws, -1)[:, :n] % n
    found = [np.corrcoef(a[p], b[p])[0, 1] for p in picks]
    return tuple(np.percentile(found, [2.5, 97.5]))


def net_exports(levels):
    """Baxter-King on each series as a share of trend output, including net exports, which can be negative and have no log."""
    return trend_shares(levels).apply(baxter_king).dropna()


def share_table(b, end=None):
    d = b[:end]
    return pd.DataFrame({"sd": d.std(), "corr_output": d.corrwith(d.Y), "share_of_output_variance": d.apply(lambda s: s.cov(d.Y)) / d.Y.var()})


def net_export_table(b):
    """The correlation of net exports with output, overall, by period and at leads and lags."""
    rows = []
    for label, start, end in (("all", None, None), ("to 2019", None, LAST_NORMAL), ("1964-1989", None, "1989Q4"), ("1990-2019", "1990Q1", LAST_NORMAL)):
        d = b[start:end]
        low, high = block_interval(d.NX, d.Y)
        rows.append({"sample": label, "corr": d.NX.corr(d.Y), "low": low, "high": high, "quarters": len(d)})
    return pd.DataFrame(rows)


def lead_lag(b):
    """Positive lead: net exports that many quarters ahead of output."""
    return pd.Series({lead: b.NX.shift(lead).corr(b.Y) for lead in range(-6, 7)}, name="corr").rename_axis("nx_leads_by").reset_index()


def recession_net_exports(b):
    rows = []
    for name, (peak, trough) in RECESSIONS.items():
        rows.append({"recession": name, "change_nx": b.NX[trough] - b.NX[peak], "change_y": b.Y[trough] - b.Y[peak]})
    return pd.DataFrame(rows)


def inventory_check(table):
    """Investment with and without inventories, under each filter, to show how much that choice matters."""
    levels = components(table)
    rows = []
    for label, investment in (("with inventories", levels.I), ("without inventories", levels.I - table[INVENTORIES])):
        logs = np.log(pd.DataFrame({"Y": levels.Y, "I": investment}))
        for name, f in FILTERS.items():
            c = logs.apply(f).dropna()
            rows.append({"investment": label, "filter": name, "sd": c.I.std(), "relative_sd": c.I.std() / c.Y.std(), "corr_output": c.I.corr(c.Y)})
    return pd.DataFrame(rows)


def main():
    OUTPUT.mkdir(exist_ok=True)
    table = read_table()
    levels = components(table)
    found = cycles(levels)
    leak = leakage(levels)
    b = net_exports(levels)
    gaps = pd.DataFrame({name: c.Y for name, c in found.items()})
    gaps["log output"] = np.log(levels.Y)
    tables = {"volatility": volatility_table(found), "recessions": recession_table(levels, found), "leakage": leakage_summary(leak),
              "revisions": revisions(levels), "net_exports": net_export_table(b), "net_exports_lead_lag": lead_lag(b),
              "net_exports_recessions": recession_net_exports(b),
              "shares": pd.concat([share_table(b).assign(sample="all"), share_table(b, LAST_NORMAL).assign(sample="to 2019")]).rename_axis("series").reset_index(),
              "output_gaps": gaps.rename_axis("quarter").reset_index(), "inventories": inventory_check(table)}
    for name, table in tables.items():
        table.to_csv(OUTPUT / f"{name}.csv", index=False, float_format="%.5f")
        print(f"\n{name}\n{table.tail(30).to_string(index=False)}" if name == "output_gaps" else f"\n{name}\n{table.to_string(index=False)}")
    gap = (levels.Y - levels[["C", "I", "G", "NX"]].sum(axis=1)) / levels.Y
    print(f"\ndata: {levels.index[0]} to {levels.index[-1]}; parts miss output by at most {gap.abs().max():.2%} ({gap.abs().idxmax()}), {gap['2000Q1':].abs().max():.2%} since 2000")
    print(f"Y/Ytrend {trend_shares(levels).Y.min():.3f} to {trend_shares(levels).Y.max():.3f}; mean NX share {trend_shares(levels).NX.mean():.3f}")


if __name__ == "__main__":
    main()
