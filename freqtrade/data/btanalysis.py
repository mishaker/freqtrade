"""
Helpers when analyzing backtest data
"""
from pathlib import Path

import numpy as np
import pandas as pd

from freqtrade.misc import json_load

# must align with columns in backtest.py
BT_DATA_COLUMNS = ["pair", "profitperc", "open_time", "close_time", "index", "duration",
                   "open_rate", "close_rate", "open_at_end", "sell_reason"]


def load_backtest_data(filename) -> pd.DataFrame:
    """
    Load backtest data file.
    :param filename: pathlib.Path object, or string pointing to the file.
    :return a dataframe with the analysis results
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.is_file():
        raise ValueError("File {filename} does not exist.")

    with filename.open() as file:
        data = json_load(file)

    df = pd.DataFrame(data, columns=BT_DATA_COLUMNS)

    df['open_time'] = pd.to_datetime(df['open_time'],
                                     unit='s',
                                     utc=True,
                                     infer_datetime_format=True
                                     )
    df['close_time'] = pd.to_datetime(df['close_time'],
                                      unit='s',
                                      utc=True,
                                      infer_datetime_format=True
                                      )
    df['profitabs'] = df['close_rate'] - df['open_rate']
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def evaluate_result_multi(results: pd.DataFrame, freq: str, max_open_trades: int) -> pd.DataFrame:
    """
    Find overlapping trades by expanding each trade once per period it was open
    and then counting overlaps
    :param results: Results Dataframe - can be loaded
    :param freq: Frequency used for the backtest
    :param max_open_trades: parameter max_open_trades used during backtest run
    :return: dataframe with open-counts per time-period in freq
    """
    dates = [pd.Series(pd.date_range(row[1].open_time, row[1].close_time, freq=freq))
             for row in results[['open_time', 'close_time']].iterrows()]
    deltas = [len(x) for x in dates]
    dates = pd.Series(pd.concat(dates).values, name='date')
    df2 = pd.DataFrame(np.repeat(results.values, deltas, axis=0), columns=results.columns)

    df2 = df2.astype(dtype={"open_time": "datetime64", "close_time": "datetime64"})
    df2 = pd.concat([dates, df2], axis=1)
    df2 = df2.set_index('date')
    df_final = df2.resample(freq)[['pair']].count()
    return df_final[df_final['pair'] > max_open_trades]
