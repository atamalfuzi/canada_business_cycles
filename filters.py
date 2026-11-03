"""The three ways of pulling a cycle out of a log series. Each takes and returns a pandas Series on the same index."""
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve


def bk_weights(k=12, low=6, high=32):
    """Baxter-King weights for lags -k to k. Passes periods from low to high quarters; the sum is forced to zero."""
    w_high, w_low = 2 * np.pi / low, 2 * np.pi / high
    j = np.arange(1, k + 1)
    side = (np.sin(j * w_high) - np.sin(j * w_low)) / (np.pi * j)
    b = np.r_[side[::-1], (w_high - w_low) / np.pi, side]
    return b - b.mean()


def baxter_king(x, k=12, low=6, high=32):
    """Two-sided moving average, so the first and last k quarters are lost."""
    out = pd.Series(np.nan, index=x.index, name=x.name)
    out.iloc[k:-k] = np.convolve(x.to_numpy(), bk_weights(k, low, high), mode="valid")
    return out


def hamilton(x, h=8, p=4):
    """Residual from regressing x on a constant and lags h to h+p-1. One-sided, so the first h+p-1 quarters are lost."""
    lags = pd.concat([x.shift(h + i) for i in range(p)], axis=1).dropna()
    X = np.c_[np.ones(len(lags)), lags.to_numpy()]
    y = x.loc[lags.index].to_numpy()
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return pd.Series(y - X @ beta, index=lags.index, name=x.name).reindex(x.index)


def hodrick_prescott(x, lamb=1600):
    """Gap from the trend that solves (I + lamb D'D) trend = x, with D the second difference. Two-sided, loses nothing."""
    n = len(x)
    D = sparse.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n))
    trend = spsolve((sparse.eye(n) + lamb * D.T @ D).tocsc(), x.to_numpy())
    return x - trend


def trend_shares(levels, output="Y"):
    """Each column divided by the geometric trend of output: a line fitted to log output, then exponentiated."""
    t = np.arange(len(levels))
    trend = np.exp(np.polyval(np.polyfit(t, np.log(levels[output]), 1), t))
    return levels.div(trend, axis=0)
