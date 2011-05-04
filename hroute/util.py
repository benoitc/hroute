# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import io
import os
import posixpath

def normalize(prefix, link):
    # anchors
    if link.startswith("#"):
        return link

    path = posixpath.normpath(os.path.join(prefix, link))
    return  path

def headers_lines(parser, headers):
    httpver = "HTTP/%s" % ".".join(map(str, parser.version()))
    new_headers = ["%s %s\r\n" % (httpver, parser.status())]
    new_headers.extend(["%s: %s\r\n" % (hname, hvalue) \
        for hname, hvalue in headers.items()])
    return new_headers

def write_chunk(to, data):
    chunk = "".join(("%X\r\n" % len(data), data, "\r\n"))
    to.write(chunk)

def write(to, data):
    to.write(data)

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

