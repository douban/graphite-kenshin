# coding: utf-8
import struct
from mock import patch
from six.moves import cPickle as pickle

from rurouni.fnv1a import get_int32_hash
from kenshin_api.carbonlink import Hash, CarbonLinkPool


def get_index(key, size):
    return get_int32_hash(key) % size


def test_hash():
    hosts = [
        ("127.0.0.1", "cache0"),
        ("127.0.0.1", "cache1"),
        ("127.0.0.1", "cache2"),
    ]

    h = Hash(hosts)
    assert h.size == len(hosts)

    keys = [
        'hosts.worker1.cpu',
        'hosts.worker2.cpu'
    ]
    for key in keys:
        assert h.get_node(key) == hosts[get_index(key, len(hosts))]


def test_hash_add_node():
    hosts = [
        ("127.0.0.1", "cache0"),
        ("127.0.0.1", "cache1"),
        ("127.0.0.1", "cache2"),
    ]

    h = Hash(hosts)
    h.add_node(("127.0.0.1", "cache3"))
    hosts.append(("127.0.0.1", "cache3"))
    assert h.size == 4
    assert h.nodes == hosts


def test_hash_remove_node():
    hosts = [
        ("127.0.0.1", "cache0"),
        ("127.0.0.1", "cache1"),
        ("127.0.0.1", "cache2"),
    ]

    h = Hash(hosts)
    node = ("127.0.0.1", "cache1")
    h.remove_node(node)
    hosts.pop(1)
    assert h.size == 2
    assert h.nodes == hosts


def test_carbon_link_poll():
    hosts = [
        '10.0.0.1:2003:cache0',
        '10.0.0.2:2003:cache1',
        '10.0.0.3:2003:cache2',
    ]
    carbonlink = CarbonLinkPool(hosts)

    with patch('socket.socket'):
        for host in hosts:
            server, port, instance = host.split(':')
            conn = carbonlink.get_connection((server, instance))
            conn.connect.assert_called_with((server, int(port)))
            carbonlink.connections[(server, instance)].add(conn)

    def mock_recv_query(size):
        data = pickle.dumps(dict(datapoints=[1, 2, 3]))
        if size == 4:
            return struct.pack('!I', len(data))
        elif size == len(data):
            return data
        else:
            raise ValueError('unexpected size %s' % size)

    conn.recv.side_effect = mock_recv_query
    datapoints = carbonlink.query('hosts.worker1.cpu')
    assert datapoints == [1, 2, 3]

    def mock_recv_get_metadata(size):
        data = pickle.dumps(dict(value='foo'))
        if size == 4:
            return struct.pack('!I', len(data))
        elif size == len(data):
            return data
        else:
            raise ValueError('unexpected size %s' % size)

    conn.recv.side_effect = mock_recv_get_metadata
    metadata = carbonlink.get_metadata('hosts.worker1.cpu', 'key')
    assert metadata == 'foo'

    def mock_recv_set_metadata(size):
        data = pickle.dumps(dict(old_value='foo', new_value='bar'))
        if size == 4:
            return struct.pack('!I', len(data))
        elif size == len(data):
            return data
        else:
            raise ValueError('unexpected size %s' % size)

    conn.recv.side_effect = mock_recv_set_metadata
    results = carbonlink.set_metadata('hosts.worker1.cpu', 'foo', 'bar')
    assert results == {'old_value': 'foo', 'new_value': 'bar'}
