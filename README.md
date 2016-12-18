Graphite-Kenshin
==================

Graphite-Kenshin is a plugin for using graphtie-api with [Kenshin](https://github.com/douban/Kenshin) storage backend.


Graphite Cluster
===================

Overview
-----------

Our graphite consists of three major components:

- [Graphite-API](https://graphite-api.readthedocs.io/en/latest/), Graphite-API is an alternative to Graphite-web, without any built-in dashboard. Its role is solely to fetch metrics from a time-series database (whisper, cyanite, etc.) and rendering graphs or JSON data out of these time series. It is meant to be consumed by any of the numerous Graphite dashboard applications.
- [Kenshin](https://github.com/douban/Kenshin.git), A time-series database alternative to Graphite Whisper with 40x improvement in IOPS.
    - Rurouni-cache, Metric processing daemon.
    - Kenshin, Time-series database library.
- [carbon-c-realy](https://github.com/douban/carbon-c-relay.git), Enhanced C implementation of Carbon relay, aggregator and rewriter.

<img src="/img/cluster.png" width="600"/>

Demo Cluster
===================

carbon-c-relay
-----------------

Build carbon-c-relay:

    $ git clone https://github.com/douban/carbon-c-relay.git
    $ cd carbon-c-relay
    $ make

Start carbon-c-realy:

    $ cd graphite-kenshin
    $ /path/to/relay -p 2001 -f ./conf/relay.conf -S 1 -H relay_0


kenshin
------------

Refer [here](https://github.com/douban/Kenshin#quick-start) to create two `Rurouni-cache` instance.

graphite-api
-----------------

Install

    $ pip install graphite-api
    $ pip install gunicorn
    $ git clone https://github.com/douban/Kenshin.git
    $ cd graphite-kenshin
    $ python setup.py install

Start graphite-api

    $ export GRAPHITE_API_CONFIG=<path/to/graphite-kenshin>/conf/graphite-api.yaml
    $ # update graphite-api.yaml
    $ gunicorn -w2 graphite_api.app:app -b 127.0.0.1:8888
