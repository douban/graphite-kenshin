#!/usr/bin/env python
# encoding: utf-8
import os
import time
import libmc
import fnmatch
import numpy as np
from os.path import (
    join, isfile, isdir, dirname, basename
)

try:
    from graphite_api.node import LeafNode, BranchNode
    from graphite_api.intervals import Interval, IntervalSet
except ImportError:
    from graphite.intervals import Interval, IntervalSet
    from graphite.node import LeafNode, BranchNode
try:
    from graphite.readers import utils as readers_utils
    BaseReader = readers_utils.BaseReader
except ImportError:
    BaseReader = object
try:
    from graphite.finders import utils as finders_utils
    BaseFinder = finders_utils.BaseFinder
except ImportError:
    BaseFinder = object

import kenshin
from kenshin_api.carbonlink import CarbonLinkPool

KENSHIN_EXT = '.hs'
KENSHINE_MC_KEY = 'kenshin:mckey:%s:%d:%d'
EXPIRE_TIME = None  # Memcached expire time
mc = None


# ========== utils =========


def is_pattern(s):
    return '*' in s or '?' in s or '[' in s or '{' in s


def _deduplicate(entries):
    yielded = set()
    for e in entries:
        if e not in yielded:
            yielded.add(e)
            yield e


def match_entries(entries, pattern):
    """A drop-in replacement for fnmatch.filter that supports pattern
    variants(ie. {foo,bar}baz = foobaz or barbaz).
    """
    v1, v2 = pattern.find('{'), pattern.find('}')
    if v1 > -1 and v2 > v1:
        variations = pattern[v1+1:v2].split(',')
        variants = [pattern[:v1] + v + pattern[v2+1:]
                    for v in variations]
        matching = []
        for variant in variants:
            matching.extend(fnmatch.filter(entries, variant))
        return list(_deduplicate(matching))
    else:
        matching = fnmatch.filter(entries, pattern)
        return matching


def fs_to_metric(path):
    dirpath = dirname(path)
    filename = basename(path)
    return join(dirpath, filename.split('.')[0]).replace(os.sep, '.')


# ========== KenshinFinder =========


class KenshinFinder(BaseFinder):

    def __init__(self, config=None):
        if config is not None:
            self.dirs = config['kenshin']['directories']
            self.carbonlink = CarbonLinkPool(config['kenshin']['carbonlink_hosts'])

            global EXPIRE_TIME, mc
            EXPIRE_TIME = int(config['kenshin']['memcached']['expire_time'])
            mc = libmc.Client(config['kenshin']['memcached']['hosts'])
        else:
            from django.conf import settings
            self.dirs = getattr(settings, 'KENSHIN_DIRECTORIES')
            self.carbonlink = CarbonLinkPool(getattr(settings, 'KENSHIN_CARBONLINK_HOSTS'))
            self.index_files = getattr(settings, 'KENSHIN_INDEX_FILES')

            global EXPIRE_TIME, mc
            EXPIRE_TIME = int(getattr(settings, 'KENSHIN_MEMCACHED_EXPIRE_TIME'))
            mc = libmc.Client(getattr(settings, 'KENSHIN_MEMCACHED_HOSTS'))

    @classmethod
    def factory(cls):
        return [KenshinFinder()]

    def find_nodes(self, query):
        clean_pattern = query.pattern.replace('\\', '')
        pattern_parts = clean_pattern.split('.')

        for root_dir in self.dirs:
            for abs_path in self._find_paths(root_dir, pattern_parts):
                relative_path = abs_path[len(root_dir):].lstrip(os.sep)
                metric_path = fs_to_metric(relative_path)

                # Now we construct and yield an appropriate Node object
                if isdir(abs_path):
                    yield BranchNode(metric_path)

                elif isfile(abs_path):
                    if abs_path.endswith(KENSHIN_EXT):
                        reader = KenshinReader(
                            abs_path, metric_path, self.carbonlink
                        )
                        yield LeafNode(metric_path, reader)

    def _find_paths(self, curr_dir, patterns):
        """Recursively generates absolute paths whose components
        underneath curr_dir match the corresponding pattern in patterns.
        """
        head, tail = patterns[0], patterns[1:]
        has_wildcard = is_pattern(head)
        using_globstar = (head == '**')

        if has_wildcard:
            entries = os.listdir(curr_dir)
        else:
            entries = [head]

        if using_globstar:
            matching_subdirs = map(lambda x: x[0], os.walk(curr_dir))
        else:
            subdirs = [e for e in entries
                       if isdir(join(curr_dir, e))]
            matching_subdirs = match_entries(subdirs, head)

        # For terminal globstar, add a pattern for all files in subdirs
        if using_globstar and not tail:
            tail = ['*']

        if tail:  # we've still got more directories to traverse
            for subdir in matching_subdirs:
                abs_path = join(curr_dir, subdir)
                for match in self._find_paths(abs_path, tail):
                    yield match

        else:  # we've got the last pattern
            if not has_wildcard:
                entries = [head + KENSHIN_EXT]
            files = [e for e in entries
                     if isfile(join(curr_dir, e))]
            matching_files = match_entries(files, head + '.*')

            for _basename in matching_files + matching_subdirs:
                yield join(curr_dir, _basename)

    def get_index(self, requestContext):
        matches = []

        for filepath in self.index_files:
            with open(filepath) as f:
                for line in f:
                    if line.endswith('\n'):
                        metric = line.split(' ', 1)[0]
                        matches.append(metric)
        matches.sort()
        return matches


# ========== KenshinReader =========


class KenshinReader(BaseReader):
    __slots__ = ('fs_path', 'metric_path', 'carbonlink')

    def __init__(self, fs_path, metric_path, carbonlink=None):
        self.fs_path = fs_path
        self.metric_path = metric_path
        self.carbonlink = carbonlink

    def get_intervals(self):
        with open(self.fs_path) as f:
            start = time.time() - kenshin.header(f)['max_retention']
        end = max(os.stat(self.fs_path).st_mtime, start)
        return IntervalSet([Interval(start, end)])

    def fetch(self, start_time, end_time):
        metric = self.metric_path
        start_interval = start_time // EXPIRE_TIME
        end_interval = end_time // EXPIRE_TIME
        key = KENSHINE_MC_KEY % (metric, start_interval, end_interval)
        data = mc.get(key)
        if not data:
            all_data = kenshin.fetch(self.fs_path, start_time, end_time)
            if not all_data:
                return

            header, time_info, vals = all_data
            vals = np.array(vals).transpose()
            tag_list = header['tag_list']
            min_step = header['archive_list'][0]['sec_per_point']

            for i, tag in enumerate(tag_list):
                k = KENSHINE_MC_KEY % (tag, start_interval, end_interval)
                v = (time_info, vals[i].tolist(), min_step)
                mc.set(k, v, time=EXPIRE_TIME)

            val = vals[tag_list.index(metric)]
        else:
            time_info, val, min_step = data

        STEP_IDX = 2
        if self.carbonlink and min_step == time_info[STEP_IDX]:
            start, end, step = time_info
            # Get cached datapoints when we fetching highest
            # resolution datapoints
            cached_datapoints = self.carbonlink.query(metric)
            for ts, v in sorted(cached_datapoints):
                # filter datapoints within [start, end)
                interval = ts - (ts % step)
                try:
                    i = int(interval - start) // step
                    val[i] = v
                except Exception:
                    pass
        return (time_info, val)
