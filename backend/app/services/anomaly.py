import pandas as pd


def detect_anomalies_iqr(
    daily_series: pd.Series
) -> pd.DataFrame:

    q1, q3 = daily_series.quantile(
        [0.25, 0.75]
    )

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    flags = (
        (daily_series < lower)
        |
        (daily_series > upper)
    )

    return pd.DataFrame(
        {
            "kwh": daily_series,
            "is_anomaly": flags,
            "lower_bound": lower,
            "upper_bound": upper
        }
    )