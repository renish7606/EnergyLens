import pandas as pd

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_percentage_error


def forecast_with_backtest(
    daily_series: pd.Series,
    forecast_days: int = 7,
    test_days: int = 14
):
    if len(daily_series) < test_days + 7:
        raise ValueError(
            "Not enough data for forecasting. "
            "Need more historical daily observations."
        )

    train = daily_series[:-test_days]
    test = daily_series[-test_days:]

    model = ExponentialSmoothing(
        train,
        trend="add",
        seasonal="add",
        seasonal_periods=7
    ).fit()

    backtest_pred = model.forecast(len(test))

    mape = mean_absolute_percentage_error(
        test,
        backtest_pred
    ) * 100

    full_model = ExponentialSmoothing(
        daily_series,
        trend="add",
        seasonal="add",
        seasonal_periods=7
    ).fit()

    future = full_model.forecast(
        forecast_days
    )

    return {
        "forecast": future.round(2).to_dict(),
        "backtest_mape_percent": round(
            mape,
            2
        )
    }