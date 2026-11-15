import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fetch_data import tidy  # noqa: E402
from forecast import holt_winters, mape, seasonal_naive, split  # noqa: E402


def monthly(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="MS"), dtype=float)


def test_mape_is_percent_error():
    assert mape([100, 200], [110, 180]) == pytest.approx(10.0)


def test_split_keeps_test_after_train_with_no_overlap():
    series = monthly(range(60))
    train, test = split(series, years_back=1)
    assert len(test) == 12
    assert train.index.max() < test.index.min()
    assert test.index.max() == series.index[-13]  # one year before the end


def test_seasonal_naive_repeats_last_year():
    train = monthly(range(36))
    assert seasonal_naive(train).tolist() == list(range(24, 36))


def test_holt_winters_follows_a_clean_seasonal_pattern():
    season = np.tile([1.0, 1.1, 0.9, 1.0, 1.2, 0.8, 1.0, 1.1, 0.9, 1.0, 1.3, 1.6], 8)
    series = monthly(100 * season)
    train, test = split(series)
    assert mape(test, holt_winters(train)) < 1.0


def test_tidy_names_industries_and_drops_unknown_codes():
    raw = pd.DataFrame({"TIME_PERIOD": ["2024-12", "2024-12"], "INDUSTRY": ["20", "99"], "OBS_VALUE": [14297.0, 1.0]})
    out = tidy(raw)
    assert out["industry"].tolist() == ["Total retail"]
    assert out["month"].iloc[0] == pd.Timestamp("2024-12-01")
