# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

"""
main proxy object used by tproxy.
"""
import io
import socket

from http_parser.parser import HttpParser
from http_parser.http import HttpStream, NoMoreData

from .lookup import HttpRoute
from .rewrite import rewrite_headers, RewriteResponse

class Route(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self._route = HttpRoute(cfg)
    
    def lookup(self, parser):
        headers = parser.get_headers()

        # get host headers
        host = None
        for hdr_name, hdr_value in headers.items():
            hl = hdr_name.lower()
            if hl == "host":
                host = hdr_value
                break
        
        return self._route.execute(host, parser.get_path())

    def rewrite_request(self, req, extra):
        try:
            if extra.get('rewrite_location', True):
                while True:
                    parser = HttpStream(req)
                    
                    prefix = extra.get('prefix', '')
                    location = parser.url()
                    if prefix:
                        try:
                            location = location.split(prefix, 1)[1] or '/'
                        except IndexError:
                            pass
                    
                    headers = rewrite_headers(parser, location,
                            [('host', extra.get('host'))])

                    if headers is None:
                        break

                    extra['path'] = parser.path()
                    req.send(headers)
                    body = parser.body_file()
                    while True:
                        data = body.read(8192)
                        if not data:
                            break
                        req.send(data)
            else:
                while True:
                    data = req.read(io.DEFAULT_BUFFER_SIZE)
                    if not data:
                        break
                    req.write(data) 
        except (socket.error, NoMoreData):
            pass

    def rewrite_response(self, resp, extra):
        try:
            if extra.get('rewrite_response', False):
                while True:
                    parser = HttpStream(resp, decompress=True)
                    
                    rw = RewriteResponse(parser, resp, extra)
                    rw.execute()

                    if not parser.should_keep_alive():
                        # close the connection.
                        break
            else:
                while True:
                    data = resp.read(io.DEFAULT_BUFFER_SIZE)
                    if not data:
                        break
                    resp.write(data)
        except (socket.error, NoMoreData):
            pass
        
    def proxy_error(self, client, e):
        msg = "HTTP/1.1 500 Server Error\r\n\r\n Server Error: '%s'" % str(e)
        client.sock.send(msg)

    def proxy(self, data):
        # parse headers
        recved = len(data)
        parser = HttpParser()
        nparsed = parser.execute(data, recved)
        if nparsed != recved:
            return {"close": True}

        if not parser.is_headers_complete():
            return

        # get remote
        return self.lookup(parser)
