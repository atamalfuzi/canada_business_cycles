"""Draw the charts: each filter's four series, output under all three, the pandemic close up, and net exports."""
import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from data import FIGURES, RECESSIONS, components, read_table
from estimate import SERIES, cycles, net_exports

INK, MUTED, BAND, GRID = "#0b0b0b", "#52514e", "#ecebe7", "#e6e5e1"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
COLOURS = dict(Y=BLUE, C=ORANGE, I=AQUA, G=YELLOW, NX=MAGENTA)
FILTER_COLOURS = {"Baxter-King": BLUE, "Hamilton": ORANGE, "Hodrick-Prescott": AQUA}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": MUTED,
                     "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "legend.frameon": False})
SOURCE = "Source: Statistics Canada table 36-10-0104; recession dates from the C.D. Howe Institute Business Cycle Council."


def save(fig, name, title, subtitle, caption):
    fig.text(0.015, 0.985, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.925, subtitle, color=MUTED, va="top")
    fig.text(0.015, 0.012, "\n".join(textwrap.wrap(caption, 138)), color=MUTED, fontsize=9, va="bottom")
    fig.savefig(FIGURES / name, dpi=200, facecolor="white")
    plt.close(fig)


def canvas(ylabel="Per cent from trend"):
    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.075, right=0.975, top=0.82, bottom=0.2)
    ax.set_ylabel(ylabel)
    return fig, ax


def bands(ax, start=None):
    """Shade each dated recession from its peak quarter to its trough quarter, naming it along the top of the plot."""
    for name, (peak, trough) in RECESSIONS.items():
        left, right = pd.Period(peak).to_timestamp(), pd.Period(trough).to_timestamp()
        if start is None or left >= pd.Period(start).to_timestamp():
            ax.axvspan(left, right, color=BAND, lw=0, zorder=0)
            ax.text(left + (right - left) / 2, 1.0, name, transform=ax.get_xaxis_transform(), ha="center", va="bottom", color=MUTED, fontsize=9)


def legend(ax, n):
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.06), ncol=n, handlelength=1.4, columnspacing=1.6, labelcolor=MUTED, borderaxespad=0)


def four_series(found, name, file, title, subtitle):
    fig, ax = canvas()
    c = found[name] * 100
    for s, label in SERIES.items():
        ax.plot(c.index.to_timestamp(), c[s], color=COLOURS[s], lw=2 if s == "Y" else 1.2, label=label, zorder=3 if s == "Y" else 2)
    ax.set_ylim(-36, 32)
    bands(ax)
    legend(ax, 4)
    save(fig, file, title, subtitle, "The charts for all three filters use the same vertical scale. " + SOURCE)


def output_gaps(found):
    fig, ax = canvas()
    for name, colour in FILTER_COLOURS.items():
        y = found[name].Y.dropna() * 100
        ax.plot(y.index.to_timestamp(), y, color=colour, lw=1.6, label=name)
    bands(ax)
    legend(ax, 3)
    save(fig, "output_gaps.png", "Output under the three filters",
         "Log output with the trend taken out, 1961 to 2026. Shaded: recessions as dated by the C.D. Howe Institute.",
         "Baxter-King and Hodrick-Prescott move together. Hamilton swings about twice as far, and its largest reading in 65 years is 2022Q2. " + SOURCE)


def pandemic(found):
    fig, ax = canvas()
    start = "2018Q1"
    marks = {"Baxter-King": ["2019Q2", "2020Q3"], "Hamilton": ["2020Q2", "2022Q2"], "Hodrick-Prescott": ["2019Q4"]}
    offsets = {"2019Q2": (0, 9), "2020Q3": (32, -8), "2020Q2": (0, -18), "2022Q2": (0, 9), "2019Q4": (14, 9)}
    for name, colour in FILTER_COLOURS.items():
        y = found[name].Y[start:"2024Q4"].dropna() * 100
        ax.plot(y.index.to_timestamp(), y, color=colour, lw=2, marker="o", ms=4, label=name, zorder=3)
        for q in marks[name]:
            ax.annotate(f"{y[q]:+.1f}".replace("-", "−"), (pd.Period(q).to_timestamp(), y[q]), xytext=offsets[q], textcoords="offset points",
                        ha="center", color=INK, fontsize=10)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_ylim(-17, 14)
    bands(ax, start)
    legend(ax, 3)
    save(fig, "pandemic.png", "One fall in output, read three ways",
         "Log output with the trend taken out, 2018 to 2024. Log output fell 13.6 points from 2019Q4 to 2020Q2 (12.7% in level).",
         "Baxter-King spreads the fall into 2019 and shows less than half of it. Hodrick-Prescott shows most of it and lifts 2019 by up to 1.7 points. "
         "Hamilton shows all of it, then a boom eight quarters later, when the fall reaches its lags. " + SOURCE)


def shares(b):
    fig, ax = canvas("Per cent of trend output")
    d = b * 100
    for s, label in (SERIES | {"NX": "Net exports"}).items():
        ax.plot(d.index.to_timestamp(), d[s], color=COLOURS[s], lw=2 if s in ("Y", "NX") else 1.1, label=label, zorder=3 if s in ("Y", "NX") else 2)
    bands(ax)
    legend(ax, 5)
    save(fig, "net_exports.png", "Against trend output, net exports swing as much as consumption",
         "Each series divided by the geometric trend of output, then Baxter-King filtered, 1964 to 2023.",
         "Net exports average about 2% of trend output, yet their filtered swings match those of consumption. " + SOURCE)


def trends(levels, found):
    """Output against what two filters treat as normal: the Hodrick-Prescott trend and Hamilton's two-year-old prediction."""
    fig, ax = canvas("Trillions of 2017 dollars, annual rate")
    start = "2005Q1"
    y = levels.Y[start:] / 1e6
    when = y.index.to_timestamp()
    ax.plot(when, y, color=INK, lw=2, label="Output", zorder=3)
    for name in ("Hodrick-Prescott", "Hamilton"):
        normal = y / np.exp(found[name].Y[start:])
        ax.plot(when, normal, color=FILTER_COLOURS[name], lw=1.6, label=f"{name}: {'trend' if name == 'Hodrick-Prescott' else 'prediction from two years earlier'}")
    bands(ax, start)
    legend(ax, 3)
    save(fig, "trends.png", "What each filter treats as normal",
         "Output from 2005 to 2026. The cycle is the gap between output and each line.",
         "Baxter-King has no single line to show: it keeps movements that repeat every 6 to 32 quarters and drops the rest. "
         "Hamilton's line dips in 2022 because it is predicting from 2020. " + SOURCE)


def main():
    FIGURES.mkdir(exist_ok=True)
    levels = components(read_table())
    found = cycles(levels)
    trends(levels, found)
    four_series(found, "Baxter-King", "baxter_king.png", "Baxter-King: investment swings about 3.7 times as far as output",
                "Periods of 6 to 32 quarters kept, 12 quarters lost at each end, 1964 to 2023. Logs, per cent from trend.")
    four_series(found, "Hamilton", "hamilton.png", "Hamilton: the same pattern, about twice as wide",
                "Residual from a regression on a constant and lags 8 to 11, 1963 to 2026. Logs, per cent from trend.")
    four_series(found, "Hodrick-Prescott", "hodrick_prescott.png", "Hodrick-Prescott: close to Baxter-King, with a sharper 2020",
                "Lambda of 1600, full sample, 1961 to 2026. Logs, per cent from trend.")
    output_gaps(found)
    pandemic(found)
    shares(net_exports(levels))


if __name__ == "__main__":
    main()
