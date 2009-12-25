# coding: utf-8
# Copyright 2009 Alexandre Fiori
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import types
from txredisapi import api
from txredisapi.protocol import RedisProtocol
from twisted.internet import defer, reactor, protocol


class _RedisFactory(protocol.ReconnectingClientFactory):
    maxDelay = 10
    protocol = RedisProtocol

    def __init__(self, pool_size):
        self.idx = 0
        self.size = 0
        self.pool = []
        self.pool_size = pool_size
        self.deferred = defer.Deferred()
        self.API = api.RedisAPI(self)

    def append(self, conn):
        self.pool.append(conn)
        self.size += 1
        if self.deferred and self.size == self.pool_size:
            self.deferred.callback(self.API)
            self.deferred = None

    def remove(self, conn):
        try:
            self.pool.remove(conn)
        except:
            pass
        self.size = len(self.pool)

    @property
    def connection(self):
        assert self.size
        conn = self.pool[self.idx % self.size]
        self.idx += 1
        return conn


def _Connection(host, port, reconnect, pool_size, lazy):
    factory = _RedisFactory(pool_size)
    factory.continueTrying = reconnect
    for x in xrange(pool_size):
        reactor.connectTCP(host, port, factory)
    return (lazy is True) and factory.API or factory.deferred

def _ShardingConnection(hosts, reconnect, pool_size, lazy):
    err = "please use a list or tuple with host:port"
    if not isinstance(hosts, (types.ListType, types.TupleType)):
        raise ValueError(err)

    connections = []
    for item in hosts:
        try:
            host, port = item.split(":")
            port = int(port)
        except:
            raise ValueError(err)
        else:
            d = _Connection(host, port, reconnect, pool_size, lazy)
            connections.append(d)

    if lazy is True:
        return api.RedisShardingAPI(connections)
    else:
        deferred = defer.DeferredList(connections)
        api.RedisShardingAPI(deferred)
        return deferred


def RedisConnection(host="localhost", port=6379, reconnect=True):
    return _Connection(host, port, reconnect, pool_size=1, lazy=False)

def lazyRedisConnection(host="localhost", port=6379, reconnect=True):
    return _Connection(host, port, reconnect, pool_size=1, lazy=True)

def RedisConnectionPool(host="localhost", port=6379, reconnect=True, pool_size=5):
    return _Connection(host, port, reconnect, pool_size, lazy=False)

def lazyRedisConnectionPool(host="localhost", port=6379, reconnect=True, pool_size=5):
    return _Connection(host, port, reconnect, pool_size, lazy=True)

def RedisShardingConnection(hosts, reconnect=True):
    return _ShardingConnection(hosts, reconnect, pool_size=1, lazy=False)

def RedisShardingConnectionPool(hosts, reconnect=True, pool_size=5):
    return _ShardingConnection(hosts, reconnect, pool_size, lazy=False)

def lazyRedisShardingConnection(hosts, reconnect=True):
    return _ShardingConnection(hosts, reconnect, pool_size=1, lazy=True)

def lazyRedisShardingConnectionPool(hosts, reconnect=True, pool_size=5):
    return _ShardingConnection(hosts, reconnect, pool_size, lazy=True)
