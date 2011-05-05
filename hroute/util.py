# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import io
import os
import posixpath
import re

from tproxy.util import parse_address

absolute_http_url_re = re.compile(r"^https?://", re.I)

def normalize(prefix, link):
    """ normalize a path """
    # anchors
    if link.startswith("#"):
        return link

    if not link.startswith('/'): 
        link = "/%s" % link
    path = posixpath.normpath("%s%s" % (prefix, link))
    return  path

def headers_lines(parser, headers):
    """ build list of header lines """
    httpver = "HTTP/%s" % ".".join(map(str, parser.version()))
    new_headers = ["%s %s\r\n" % (httpver, parser.status())]
    new_headers.extend(["%s: %s\r\n" % (hname, hvalue) \
        for hname, hvalue in headers.items()])
    return new_headers

def get_host(addr, is_ssl=False):
    """ return a correct Host header """
    host = addr[0]
    if addr[1] != (is_ssl and 443 or 80):
        host = "%s:%s" % (host, addr[1])
    return host

def base_uri(host, is_ssl=False):
    """ return the host uri """
    if is_ssl:
        scheme = "https"
    else:
        scheme = "http"
    return "%s://%s" % (scheme, host)

def write_chunk(to, data):
    """ send a chunk encoded """
    chunk = "".join(("%X\r\n" % len(data), data, "\r\n"))
    to.writeall(chunk)

def write(to, data):
    to.writeall(data)

def send_body(to, body, chunked=False):
    if chunked:
        _write = write_chunk
    else:
        _write = write

    while True:
        data = body.read(io.DEFAULT_BUFFER_SIZE)
        if not data:
            break
        _write(to, data)

    if chunked:
        _write(to, "")

