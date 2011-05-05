# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import os

try:
    import simplejson as json
except ImportError:
    import json

DEFAULT_CONTROLS =  {
        "rewrite_location": True,
        "rewrite_response": False
}

class HttpRoute(object):

    def __init__(self, cfg):
        self.cfg = cfg
        self.cfg.load_routes()

    def execute(self, host, path):
        # refresh routes if needed.
        self.cfg.load_routes()

        extra = {}
        found_name = None
        route_conf = None
        for rhost, name in self.cfg.hosts:
            if rhost.match(host):
                found_name = name
                routes = self.cfg.routes.get(name)
                if not routes:
                    break
                for route, spec, conf in routes:
                    m = spec.match(path)
                    if m:
                        route_conf = conf
                        extra = DEFAULT_CONTROLS.copy()
                        extra.update(conf)
                        if m.group(1):
                            extra['prefix'] = path.split(m.group(1))[0]
                        else:
                            extra['prefix'] = path
                        
                        route_conf['extra'] = extra
                        break
        if not route_conf:
            return {'close': 'HTTP/1.1 502 Gateway Error\r\n\r\nNo target found'}

        return route_conf 
