"""Reading the table, building the series and the helpers behind the tables. No downloads."""
import io
import zipfile

import numpy as np
import pandas as pd
import pytest

import data
from estimate import block_interval, quarters_below, smooth_pandemic

SA = "Seasonally adjusted at annual rates"


def table_zip(tmp_path, rows):
    path = tmp_path / "table.zip"
    columns = ["REF_DATE", "Prices", "Seasonal adjustment", "Estimates", "VALUE", "TERMINATED"]
    text = io.StringIO()
    pd.DataFrame(rows, columns=columns).to_csv(text, index=False)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("36100104.csv", text.getvalue())
    return path


def test_read_table_keeps_only_the_current_chained_seasonally_adjusted_series(tmp_path):
    t = data.read_table(table_zip(tmp_path, [
        ("1961-01", "Chained (2017) dollars", SA, data.GDP, 100.0, None),
        ("1961-04", "Chained (2017) dollars", SA, data.GDP, 101.0, None),
        ("1961-01", "Chained (2012) dollars", SA, data.GDP, 90.0, "t"),
        ("1961-01", "Current prices", SA, data.GDP, 50.0, None),
        ("1961-01", "Chained (2017) dollars percentage change", SA, data.GDP, 1.0, None),
        ("1961-01", "Chained (2017) dollars", "Unadjusted", data.GDP, 80.0, None)]))
    assert t[data.GDP].tolist() == [100.0, 101.0]
    assert [str(q) for q in t.index] == ["1961Q1", "1961Q2"]


def test_read_table_stops_if_two_chained_bases_are_live(tmp_path):
    with pytest.raises(ValueError):
        data.read_table(table_zip(tmp_path, [("1961-01", "Chained (2017) dollars", SA, data.GDP, 100.0, None),
                                             ("1961-01", "Chained (2012) dollars", SA, data.GDP, 90.0, None)]))


def source(**changes):
    row = {data.GDP: 100.0, data.FINAL: 70.0, data.DURABLES: 5.0, data.GOV_C: 20.0, data.GFCF: 25.0, data.GOV_I: 3.0,
           data.INVENTORIES: 2.0, data.EXPORTS: 30.0, data.IMPORTS: 29.0} | changes
    return pd.DataFrame([row])


def test_components_follow_the_definitions():
    p = data.components(source()).iloc[0]
    assert p.C == 70 - 5 - 20
    assert p.I == 25 + 5 + 2 - 3
    assert p.G == 20 + 3
    assert p.NX == 30 - 29


def test_components_stop_on_a_missing_quarter():
    with pytest.raises(ValueError):
        data.components(source(**{data.INVENTORIES: np.nan}))


def test_recession_dates_are_in_order_and_in_the_data():
    ends = [pd.Period(q, freq="Q") for pair in data.RECESSIONS.values() for q in pair]
    assert ends == sorted(ends) and ends[0] > pd.Period("1961Q1", freq="Q")


def test_smooth_pandemic_is_a_straight_line_between_the_ends():
    index = pd.period_range("2019Q1", "2022Q4", freq="Q")
    y = pd.Series(np.arange(len(index), dtype=float), index=index)
    jagged = y.copy()
    jagged["2020Q1":"2021Q3"] = -50.0
    assert smooth_pandemic(jagged).tolist() == pytest.approx(y.tolist())


def test_quarters_below_counts_from_the_low_to_zero():
    index = pd.period_range("2000Q1", periods=5, freq="Q")
    gap = pd.Series([-3.0, -2.0, -1.0, 0.5, -1.0], index=index)
    assert quarters_below(gap, index[0]) == 3
    assert np.isnan(quarters_below(gap.iloc[:3], index[0]))


def test_block_interval_covers_the_correlation_of_related_series():
    rng = np.random.default_rng(0)
    a = rng.normal(size=300)
    b = a + rng.normal(size=300)
    low, high = block_interval(a, b, draws=500)
    assert low < np.corrcoef(a, b)[0, 1] < high and low > 0
