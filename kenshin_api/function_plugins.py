#!/usr/bin/env python
# encoding: utf-8

from graphite.render.functions import transformNull, removeBelowValue
from graphite.render.attime import parseTimeOffset
from graphite.functions.params import Param, ParamTypes


def to_seconds(delta):
    """
    Convert a timedelta object into seconds
    (same as delta.total_seconds() in Python 2.7+)
    """
    return abs(delta.seconds + delta.days * 86400)


def smooth(requestContext, seriesList, intervalString='5min'):
    results = []
    interval = int(to_seconds(parseTimeOffset(intervalString)))

    for series in seriesList:
        if series.step < interval:
            values_per_point = interval // series.step
            series.consolidate(values_per_point)
            series.step = interval
        results.append(series)

    return results


smooth.group = 'Custom'
smooth.params = [
    Param('seriesList', ParamTypes.seriesList, required=True),
    Param('intervalString', ParamTypes.interval, required=True)
]


def points(requestContext, seriesList, maxPoints):
    results = []
    for series in seriesList:
        if not maxPoints or len(series) < maxPoints:
            results.append(series)
            continue
        if len(series) % maxPoints != 0:
            values_per_point = len(series) // maxPoints + 1
        else:
            values_per_point = len(series) // maxPoints
        series.consolidate(values_per_point)
        series.step = series.step * values_per_point
        results.append(series)
    return results


points.group = 'Custom'
points.params = [
    Param('seriesList', ParamTypes.seriesList, required=True),
    Param('maxPoints', ParamTypes.integer, required=True)
]


SeriesFunctions = {
    'treatNoneAs': transformNull,
    'points': points,

    # Deprecated
    'smooth': smooth,
    'only_burst': removeBelowValue,
}
