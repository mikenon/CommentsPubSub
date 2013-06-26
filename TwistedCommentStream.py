# coding: utf-8
#
# Copyright 2009 Alexandre Fiori
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
# #
# Based on https://github.com/fiorix/twisted-twitter-stream by Alexandre Fiori 
# #
__author__ = "mikenon, Alexandre Fiori"
__version__ = "0.0.1"

import base64, urllib
from twisted.protocols import basic
from twisted.internet import defer, reactor, protocol

try:
    import simplejson as _json
except ImportError:
    try:
        import json as _json
    except ImportError:
        raise RuntimeError("A JSON parser is required, e.g., simplejson at "
                           "http://pypi.python.org/pypi/simplejson/")

class CommentReceiver(object):
    def connectionMade(self):
        pass
    
    def connectionLost(self, why):
        pass

    def connectionFailed(self, why):
        pass

    def commentReceived(self, comment):
        raise NotImplementedError

    def _registerProtocol(self, protocol):
        self._streamProtocol = protocol

    def disconnect(self):
        if hasattr(self, "_streamProtocol"):
            self._streamProtocol.factory.continueTrying = 0
            self._streamProtocol.transport.loseConnection()
        else:
            raise RuntimeError("not connected")


class _CommentStreamProtocol(basic.LineReceiver):
    delimiter = "\r\n"

    def __init__(self):
        self.in_header = True
        self.header_data = []
        self.status_data = ""
        self.status_size = None

    def connectionMade(self):
        self.transport.write(self.factory.header)
        self.factory.consumer._registerProtocol(self)
        
    def connectionLost(self, reason):
        print reason
        self.factory.consumer.connectionLost(reason)

    def lineReceived(self, line):
        while self.in_header:
            if line:
                self.header_data.append(line)
            else:
                http, status, message = self.header_data[0].split(" ", 2)
                status = int(status)
                if status == 200:
                    self.factory.consumer.connectionMade()
                    self.factory.resetDelay()
                else:
                    print 'failing connection'
                    print http
                    print status
                    print message
                    self.factory.continueTrying = 0
                    self.transport.loseConnection()
                    self.factory.consumer.connectionFailed(RuntimeError(status, message))

                self.in_header = False
            break
        else:
            try:
                self.status_size = int(line, 16)
                self.setRawMode()
            except:
                pass

    def rawDataReceived(self, data):
        if self.status_size is not None:
            data, extra = data[:self.status_size], data[self.status_size:]
            self.status_size -= len(data)
        else:
            extra = ""

        self.status_data += data
        if self.status_size == 0:
            try:
                # ignore newline keep-alive
                comment = _json.loads(self.status_data)
            except:
                pass
            else:
                self.factory.consumer.commentReceived(comment)
            self.status_data = ""
            self.status_size = None
            self.setLineMode(extra)


class _CommentStreamFactory(protocol.ReconnectingClientFactory):
    # See: http://twistedmatrix.com/documents/current/api/twisted.internet.protocol.ReconnectingClientFactory.html
    maxDelay = 120
    protocol = _CommentStreamProtocol

    def __init__(self, consumer):
        if isinstance(consumer, CommentReceiver):
            self.consumer = consumer
        else:
            raise TypeError("consumer should be an instance of TwistedCommentStream.CommentReceiver")
    
    def make_header(self, method, uri, postdata=""):
        header = [
            "%s %s HTTP/1.1" % (method, uri),
            "User-Agent: twisted comment stream by /u/stickytruth",
            "Host: dev.redditanalytics.com",
        ]

        if method == "GET":
            self.header = "\r\n".join(header) + "\r\n\r\n"

def comments(consumer):
    cs = _CommentStreamFactory(consumer)
    cs.make_header("GET", "/stream/")
    reactor.connectTCP("dev.redditanalytics.com", 80, cs)

def subreddit(consumer, subreddit=False):
    qs = []
    if subreddit != False:
        qs.append("subreddit=%s" % urllib.quote(subreddit))

    cs = _CommentStreamFactory(consumer)
    cs.make_header("GET", "/stream/?" + "&".join(qs))
    reactor.connectTCP("dev.redditanalytics.com", 80, cs)