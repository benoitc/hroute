# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import io
import re
import urlparse

from http_parser.http import ParserError, NoMoreData
try:
    from lxml import etree
    import lxml.html
except ImportError:
    raise ImportError("""lxml isn't installed

        pip install lxml
""")

absolute_http_url_re = re.compile(r"^https?://", re.I)

from .util import headers_lines, normalize, send_body

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
       
        # handle redirection
        status_int = self.parser.status_code()

        if status_int in (301, 302, 303):
            location = headers.get('location')
            if location.startswith(self.base):
                rel = "%s%s" % (self.prefix, location.split(self.base)[1])
                headers['location'] = urlparse.urljoin(self.local_base, rel)
            elif location.startswith("/"):
                # bugged server
                rel = "%s%s" % (self.prefix, location)
                headers['location'] = urlparse.urljoin(self.local_base, rel)

            return False, headers_lines(self.parser, headers)

        # rewrite location
        prefix = self.extra.get('prefix')
        if prefix is not None and "location" in headers:
            location = headers['location']
            if not location.startswith('/'):
                location = "/%s" % location
            headers['location'] = "%s%s" % (self.prefix, location)

        # can we rewrite the links?
        ctype = headers.get('content-type')
        if ctype is not None:
            ctype = ctype.split(';', 1)[0].strip()

        if ctype in HTML_CTYPES:
            rewrite = True
            for h in ('content-length', 'transfer-encoding'):
                if h in headers:
                    del headers[h]
        else:
            rewrite = False
        headers['connection'] = 'close'
        return (rewrite, headers_lines(self.parser, headers))

    def rewrite_link(self, link):
        if not absolute_http_url_re.match(link):
            link = normalize(self.prefix, link)
        elif link.startswith(self.base):
            rel = "%s%s" % (self.prefix, link.split(self.base)[1])
            link = urlparse.urljoin(self.local_base, rel)
        return link

    def execute(self):
        rewrite, headers = self.rewrite_headers()
        if not headers:
            return
        
        if rewrite:
            body = self.parser.body_string()
            if not body:
                rewritten_body = ''
            else:
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
            
            # finally send response.
            headers.append('Content-Length: %s\r\n' % len(rewritten_body))
            headers.extend(["\r\n", rewritten_body])
            
            stream = io.BytesIO("".join(headers))
            while True:
                data = stream.read(io.DEFAULT_BUFFER_SIZE)
                if not data:
                    break
                self.resp.send(data)
        else:
            self.resp.send("".join(headers) + "\r\n")
            body = self.parser.body_file()
            send_body(self.resp, body, self.parser.is_chunked())
