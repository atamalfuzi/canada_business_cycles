"""The filters against properties they must have by construction, and against statsmodels as a second implementation."""
import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.filters.bk_filter import bkfilter
from statsmodels.tsa.filters.hp_filter import hpfilter

from filters import baxter_king, bk_weights, hamilton, hodrick_prescott, trend_shares


def walk(n=200, seed=1):
    index = pd.period_range("1961Q1", periods=n, freq="Q")
    return pd.Series(np.cumsum(np.random.default_rng(seed).normal(0.005, 0.01, n)), index=index)


def wave(period, n=400):
    return pd.Series(np.sin(2 * np.pi * np.arange(n) / period), index=pd.period_range("1961Q1", periods=n, freq="Q"))


def test_bk_weights_are_symmetric_and_sum_to_zero():
    w = bk_weights(k=12, low=6, high=32)
    assert len(w) == 25
    assert w == pytest.approx(w[::-1])
    assert w.sum() == pytest.approx(0, abs=1e-12)


def test_bk_loses_twelve_quarters_at_each_end():
    out = baxter_king(walk())
    assert out.iloc[:12].isna().all() and out.iloc[-12:].isna().all() and out.iloc[12:-12].notna().all()


def test_bk_removes_a_straight_line():
    line = pd.Series(np.arange(100.0), index=pd.period_range("1961Q1", periods=100, freq="Q"))
    assert baxter_king(line).dropna().abs().max() < 1e-9


@pytest.mark.parametrize("period,low,high", [(12, 0.9, 1.1), (3, 0, 0.1), (200, 0, 0.1)])
def test_bk_keeps_the_band_and_drops_the_rest(period, low, high):
    x = wave(period)
    gain = baxter_king(x).dropna().std() / x.std()
    assert low <= gain <= high


def test_bk_matches_statsmodels():
    x = walk()
    assert baxter_king(x).dropna().to_numpy() == pytest.approx(bkfilter(x.to_numpy(), 6, 32, 12), abs=1e-10)


def test_hamilton_residuals_are_orthogonal_to_the_constant_and_each_lag():
    x = walk()
    e = hamilton(x).dropna()
    assert e.mean() == pytest.approx(0, abs=1e-10)
    for lag in (8, 9, 10, 11):
        assert np.dot(e, x.shift(lag).loc[e.index]) == pytest.approx(0, abs=1e-8)


def test_hamilton_uses_lags_8_to_11_only():
    x = walk()
    e = hamilton(x)
    assert e.iloc[:11].isna().all() and e.iloc[11:].notna().all()
    X = np.column_stack([np.ones(len(x) - 11)] + [x.shift(lag).iloc[11:] for lag in (8, 9, 10, 11)])
    beta = np.linalg.lstsq(X, x.iloc[11:], rcond=None)[0]
    assert e.iloc[11:].to_numpy() == pytest.approx(x.iloc[11:].to_numpy() - X @ beta)


def test_hp_cycle_is_orthogonal_to_a_line():
    """(I + lamb D'D) trend = x means x - trend = lamb D'D trend, and D sends a constant and a line to zero."""
    c = hodrick_prescott(walk())
    assert c.sum() == pytest.approx(0, abs=1e-8)
    assert np.dot(c, np.arange(len(c))) == pytest.approx(0, abs=1e-6)


def test_hp_matches_statsmodels():
    x = walk()
    assert hodrick_prescott(x).to_numpy() == pytest.approx(hpfilter(x.to_numpy(), lamb=1600)[0], abs=1e-8)


def test_trend_shares_of_an_exact_exponential_are_one():
    t = np.arange(40)
    levels = pd.DataFrame({"Y": 100 * np.exp(0.01 * t), "NX": -5.0 * np.exp(0.01 * t)})
    shares = trend_shares(levels)
    assert shares.Y.to_numpy() == pytest.approx(np.ones(40))
    assert shares.NX.to_numpy() == pytest.approx(-0.05 * np.ones(40))
