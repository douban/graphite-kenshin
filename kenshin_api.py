#!/usr/bin/env python
# encoding: utf-8

import libmc
import kenshin
import numpy as np

from graphite_api.node import LeafNode

KENSHINE_MC_KEY = 'kenshin:mckey:%s:%d:%d'
EXPIRE_TIME = 20  # Memcached expire time: 20s
LOCAL_MEMCACHE = ['localhost:11211']

mc = libmc.Client(LOCAL_MEMCACHE)


class KenshinLeafNode(LeafNode):
    pass


class KenshinReader(object):
    __slots__ = ('fs_path', 'real_metric', 'carbonlink')

    def __init__(self, fs_path, real_metric, carbonlink=None):
        self.fs_path = fs_path
        self.real_metric = real_metric
        self.carbonlink = carbonlink

    def fetch(self, start_time, end_time):
        metric = self.real_metric
        start_interval = start_time // EXPIRE_TIME
        end_interval = end_time // EXPIRE_TIME
        key =  KENSHINE_MC_KEY % (metric, start_interval, end_interval)
        data = mc.get(key)
        if not data:
            all_data = kenshin.fetch(self.fs_path, start_time, end_time)
            if not all_data:
                return

            header, time_info, vals = all_data
            vals = np.array(vals).transpose()
            tag_list = header['tag_list']
            min_step = header['archive_list'][0]['sec_per_point']

            for i, tag in tag_list:
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


class KenshinFinder(object):

    def __init__(self, config):
        self.dirs = config['kenshin']['directories']



if __name__ == '__main__':
    pass
