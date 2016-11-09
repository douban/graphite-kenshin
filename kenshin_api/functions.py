#!/usr/bin/env python
# encoding: utf-8

from graphite_api.functions import transformNull, removeBelowValue
from graphite_api.utils import to_seconds
from graphite_api.render.attime import parseTimeOffset


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


SeriesFunctions = {
    'treatNoneAs': transformNull,
    'points': points,

    # Deprecated
    'smooth': smooth,
    'only_burst': removeBelowValue,
}
