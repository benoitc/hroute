# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import io
import re

from http_parser.http import ParserError, NoMoreData
try:
    from lxml import etree
    import lxml.html
except ImportError:
    raise ImportError("""lxml isn't installed

        pip installl lxml
""")

absolute_http_url_re = re.compile(r"^https?://", re.I)

from .util import normalize

HTML_CTYPES = ( 
    "text/html",
    "application/xhtml+xml",
    "application/xml"
)

def rewrite_headers(parser, location, values=None):
    headers = parser.headers()
    values = values or []
    
    new_headers = []

    if values and values is not None:
        for hname, hvalue in values:
            headers[hname] = hvalue

    httpver = "HTTP/%s" % ".".join(map(str, 
                parser.version()))

    new_headers = ["%s %s %s\r\n" % (parser.method(), location, 
        httpver)]

    new_headers.extend(["%s: %s\r\n" % (hname, hvalue) \
            for hname, hvalue in headers.items()])

    return "".join(new_headers) + "\r\n"


def write_chunk(to, data):
    chunk = "".join(("%X\r\n" % len(data), data, "\r\n"))
    to.write(chunk)

def write(to, data):
    to.write(data)

class RewriteResponse(object):

    def __init__(self, parser, resp, extra):
        self.parser = parser
        self.resp = resp
        self.extra = extra
        self.prefix = extra.get('prefix')
        if self.prefix is not None and self.prefix.endswith('/'):
            self.prefix = self.prefix[:-1]

        if 'ssl_keyfile' in extra:
            scheme = "https"
        else:
            scheme = "http"

        self.base = "%s://%s" % (scheme, extra['host'])
        if extra['remote'][1] not in (80, 443):
            self.base = "%s:%s" % (self.base, extra['remote'][1])
        
        self.local_base = "%s://%s%s" % (
            extra.get('listen_ssl', False) and "https" or "http",
            extra['listen'][0],
            extra['listen'][1] in (80, 443) and "" or ":%s" % extra['listen'][1]
        )

    def rewrite_headers(self):
        try:
            headers = self.parser.headers()
        except (ParserError, NoMoreData):
            return False, None
        
        # rewrite location
        prefix = self.extra.get('prefix')
        if prefix is not None and "location" in headers:
            location = headers['location']
            if not location.startswith('/'):
                location = "/%s" % location
            headers['location'] = "%s%s" % (self.prefix, location)

        # can we rewrite the links?
        if headers.get('content-type') in HTML_CTYPES:
            rewrite = True
            for h in ('content-length', 'transfer-encoding'):
                if h in headers:
                    del headers[h]
        else:
            rewrite = False

        
            
        httpver = "HTTP/%s" % ".".join(map(str, self.parser.version()))
        new_headers = ["%s %s\r\n" % (httpver, self.parser.status())]
        new_headers.extend(["%s: %s\r\n" % (hname, hvalue) \
            for hname, hvalue in headers.items()])

        return (rewrite, new_headers)

    def rewrite_link(self, link):
        if not absolute_http_url_re.match(link):
            return normalize(self.prefix, link)
        else:
            if link.startswith(self.base):
                rel = link.split(self.base)[1]
                return normalize(self.prefix, link)
        return link

    def execute(self):
        rewrite, headers = self.rewrite_headers()
        if not headers:
            return
        
        self.resp.send(headers)
        if rewrite:
            body = self.parser.body_string()
            html = lxml.html.fromstring(body)

            # rewrite links to absolute 
            html.rewrite_links(self.rewrite_link)


            # add base
            absolute_path = "%s%s" % (self.local_base,
                    self.extra.get('path', ''))
            
            old_base = html.find(".//base")
            base = etree.Element("base")
            base.attrib['href'] = absolute_path 

            if not old_base:
                head = html.find(".//head")
                head.append(base)
            
            # modify response
            rewritten_body = lxml.html.tostring(html)
            headers.append('Content-Length: %s\r\n' %
                        len(rewritten_body))

            self.resp.send("".join(headers) + "\r\n%s" % rewritten_body)

        else:
            self.resp.send("".join(headers) + "\r\n")
            body = self.parser.body_file()

            if  self.parser.is_chunked():
                _write = write_chunk
            else:
                _write = write

            while True:
                data = body.read(io.DEFAULT_BUFFER_SIZE)
                if not data:
                    break
                _write(self.resp, data)

            if self.parser.is_chunked():
                _write(self.resp, "")
