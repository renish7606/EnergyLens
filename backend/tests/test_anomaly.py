import pandas as pd

from app.services.anomaly import (
    detect_anomalies_iqr
)


def test_flags_obvious_spike():

    series = pd.Series(
        [10, 11, 9, 10, 12, 10, 50]
    )

    result = detect_anomalies_iqr(
        series
    )

    assert (
        result.iloc[-1]["is_anomaly"]
        == True
    )

    assert (
        result.iloc[0]["is_anomaly"]
        == False
    )