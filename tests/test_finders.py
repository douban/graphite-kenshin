# coding: utf-8
import os
import shutil
import pytest

from graphite_api.app import app
from graphite_api.storage import Store

import kenshin
from kenshin_api import KenshinFinder

DATA_DIR = '/tmp/graphite-kenshin-data.{0}'.format(os.getpid())
KENSHIN_DIR = os.path.join(DATA_DIR, 'kenshin')


_listdir_counter = 0
_original_listdir = os.listdir


def listdir_mock(d):
    global _listdir_counter
    _listdir_counter += 1
    return _original_listdir(d)


@pytest.fixture(scope='function')
def setup_teardown():
    os.makedirs(KENSHIN_DIR)
    app.config['TESTING'] = True
    kenshin_conf = {
        'kenshin': {
            'directories': [KENSHIN_DIR],
            'carbonlink_hosts': [],
            'memcached': {
                'expire_time': 20,
                'hosts': ['127.0.0.1']
            }
        }
    }
    app.config['GRAPHITE']['store'] = Store([KenshinFinder(kenshin_conf)])
    yield
    shutil.rmtree(DATA_DIR)


def create_kenshin_file(db_path):
    tag_list = []
    archive_list = [(1, 6), (3, 6)]
    x_file_factor = 1.0
    agg_name = 'average'
    kenshin.create(db_path, tag_list, archive_list, x_file_factor, agg_name)


def test_kenshin_finder(setup_teardown):
    for db in (
        ('kenshin_finder', 'foo.hs'),
        ('kenshin_finder', 'foo', 'bar', 'baz.hs'),
        ('kenshin_finder', 'bar', 'baz', 'baz.hs'),
    ):
        db_path = os.path.join(KENSHIN_DIR, *db)
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        create_kenshin_file(db_path)

    try:
        global _listdir_counter
        os.listdir = listdir_mock
        store = app.config['GRAPHITE']['store']

        _listdir_counter = 0
        nodes = store.find('kenshin_finder.foo')
        assert len(list(nodes)) == 2
        assert _listdir_counter == 0

        _listdir_counter = 0
        nodes = store.find('kenshin_finder.foo.bar.baz')
        assert len(list(nodes)) == 1
        assert _listdir_counter == 0

        _listdir_counter = 0
        nodes = store.find('kenshin_finder.*.ba?.{baz,foo}')
        assert len(list(nodes)) == 2
        assert _listdir_counter == 5

    finally:
        os.listdir = _original_listdir


def test_globstar(setup_teardown):
    store = app.config['GRAPHITE']['store']
    query = 'x.**.x'
    hits = ['x.x', 'x._.x', 'x._._.x']
    misses = ['x.x.o', 'o.x.x', 'x._.x._.o', 'o._.x._.x']
    for path in hits + misses:
        db_path = os.path.join(KENSHIN_DIR, path.replace('.', os.sep))
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        create_kenshin_file(db_path + '.hs')
    paths = [node.path for node in store.find(query, local=True)]
    for hit in hits:
        assert hit in paths
    for miss in misses:
        assert miss not in paths


def test_multiple_globstars(setup_teardown):
    store = app.config['GRAPHITE']['store']
    query = "y.**.y.**.y"
    hits = [
        "y.y.y", "y._.y.y", "y.y._.y", "y._.y._.y",
        "y._._.y.y", "y.y._._.y"
    ]
    misses = [
        "y.o.y", "o.y.y", "y.y.o", "o.y.y.y",  "y.y.y.o",
        "o._.y._.y", "y._.o._.y", "y._.y._.o"
    ]
    for path in hits + misses:
        db_path = os.path.join(KENSHIN_DIR, path.replace(".", os.sep))
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        create_kenshin_file(db_path + '.hs')

    paths = [node.path for node in store.find(query, local=True)]
    for hit in hits:
        assert hit in hits
    for miss in misses:
        assert miss not in paths


def test_terminal_globstar(setup_teardown):
    store = app.config['GRAPHITE']['store']
    query = "z.**"
    hits = ["z._", "z._._", "z._._._"]
    misses = ["z", "o._", "o.z._", "o._.z"]
    for path in hits + misses:
        db_path = os.path.join(KENSHIN_DIR, path.replace(".", os.sep))
        if not os.path.exists(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
        create_kenshin_file(db_path + '.hs')

    paths = [node.path for node in store.find(query, local=True)]
    for hit in hits:
        assert hit in hits
    for miss in misses:
        assert miss not in paths
