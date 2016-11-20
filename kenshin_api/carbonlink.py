#!/usr/bin/env python
# encoding: utf-8
import time
import socket
import struct
from six.moves import cPickle as pickle
from fnv1a import get_int32_hash


class Hash(object):

    def __init__(self, nodes):
        self.nodes = nodes
        self.size = len(self.nodes)

    def add_node(self, node):
        self.nodes.append(node)
        self.size += 1

    def remove_node(self, node):
        try:
            i = self.nodes.index(node)
        except ValueError:
            pass
        else:
            self.nodes.pop(i)
            self.size -= 1

    def get_node(self, key):
        i = get_int32_hash(key) % self.size
        return self.nodes[i]


class CarbonLinkPool(object):

    def __init__(self, hosts, timeout=1):
        self.hosts = []
        self.ports = {}
        for host in hosts:
            server, port, instance = host.split(':')
            self.hosts.append((server, instance))
            self.ports[(server, instance)] = int(port)

        self.timeout = float(timeout)

        self.hash_ring = Hash(self.hosts)
        self.connections = {}
        self.last_failure = {}
        # Create a connection pool for each host
        for host in self.hosts:
            self.connections[host] = set()

    def select_host(self, metric):
        """
        Returns the carbon host that has data for the given metric.
        """
        return self.hash_ring.get_node(metric)

    def get_connection(self, host):
        # First try to take one out of the pool for this host
        server, instance = host
        port = self.ports[host]
        pool = self.connections[host]
        try:
            return pool.pop()
        except KeyError:
            pass  # nothing left in the pool, gotta make a new connection

        connection = socket.socket()
        connection.settimeout(self.timeout)
        try:
            connection.connect((server, port))
        except Exception:
            self.last_failure[host] = time.time()
            raise

        connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        return connection

    def query(self, metric):
        if not self.hosts:
            return []
        request = dict(type='cache-query', metric=metric)
        results = self.send_request(request)
        return results['datapoints']

    def get_metadata(self, metric, key):
        request = dict(type='get-metadata', metric=metric, key=key)
        results = self.send_request(request)
        return results['value']

    def set_metadata(self, metric, key, value):
        request = dict(type='set-metadata',
                       metric=metric,
                       key=key,
                       value=value)
        results = self.send_request(request)
        return results

    def send_request(self, request):
        metric = request['metric']
        serialized_request = pickle.dumps(request, protocol=2)
        len_prefix = struct.pack('!L', len(serialized_request))
        request_packet = len_prefix + serialized_request
        results = {}
        results.setdefault('datapoints', [])

        host = self.select_host(metric)
        conn = self.get_connection(host)
        try:
            conn.sendall(request_packet)
            result = self.recv_response(conn)
        except Exception:
            self.last_failure[host] = time.time()
            raise
        else:
            self.connections[host].add(conn)
            if 'error' in result:
                raise CarbonLinkRequestError(result['error'])
        return result

    def recv_response(self, conn):
        len_prefix = recv_exactly(conn, 4)
        body_size = struct.unpack('!L', len_prefix)[0]
        body = recv_exactly(conn, body_size)
        return pickle.loads(body)


class CarbonLinkRequestError(Exception):
    pass


# Socket helper functions
def recv_exactly(conn, num_bytes):
    buf = b''
    while len(buf) < num_bytes:
        data = conn.recv(num_bytes - len(buf))
        if not data:
            raise Exception('Connection lost')
        buf += data
    return buf
