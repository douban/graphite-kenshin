# encoding: utf-8
import time
import copy
from graphite_api.render.datalib import TimeSeries
from kenshin_api.functions import smooth, points


def _generate_series_list(config=(
    range(101),
    range(2, 103),
    [1] * 2 + [None] * 90 + [1] * 2 + [None] * 7,
    []
)):
    series_list = []
    now = int(time.time())
    for i, c in enumerate(config):
        name = "collectd.test-db{0}.load.value".format(i + 1)
        series = TimeSeries(name, now - 101, now, 1, c)
        series.pathExpression = name
        series_list.append(series)
    return series_list


def test_points():
    series_list = _generate_series_list()
    results = points({}, copy.deepcopy(series_list), 2)
    first_series = list(results[0])
    assert len(first_series) == 2
    assert first_series == [25.0, 75.5]


def test_smooth():
    series_list = _generate_series_list()
    results = smooth({}, copy.deepcopy(series_list), '50s')
    first_series = list(results[0])
    assert len(first_series) == 3
    assert first_series == [24.5, 74.5, 100.0]
