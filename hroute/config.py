# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.
import os
import re


from tproxy import config

try:
    import simplejson as json
except ImportError:
    import json

ROUTE_RE = re.compile("^([^(].*)\(.*\)$")


def validate_path(value):
    if value is not None and not os.path.exists(value):
        raise IOError("spool directory %s doesn't exist" % value)
    return value

class SpoolDir(config.Setting):
    name = "spooldir"
    section = "Spool Directory"
    cli = ["-s", "--spool"]
    meta = "STRING"
    validator = validate_path
    default = None 
    desc = """\
        The path to a hroute sppol dir.
        
        Used to set hroute rules and users. 
        """

class RouteConfig(config.Config):

    def __init__(self, usage=None):
        super(RouteConfig, self).__init__(usage=usage)

        self._spooldir = None
        self.routes = {}
        self.hosts = []
        self.rmtime = None

    def get_spooldir(self):
        if self._spooldir:
            return self._spooldir

        spooldir = self.spooldir
        if not spooldir:
            if not os.path.exists('/var/spool/hroute'):
                raise IOError("spool directory '/var/spool/hroute'"
                    "doesn't exist\n")
            spooldir = '/var/spool/hroute'
        self._spooldir = spooldir
        return self._spooldir

    def load_routes(self):
        """ load route from configuration file """
        fname = os.path.join(self.get_spooldir(), 'routes')
        if not os.path.exists(fname):
            return

        # do we need to relad routes ?
        mtime = os.stat(fname).st_mtime
        if self.rmtime == mtime:
            return
        self.rmtime = mtime

        # build rules
        with open(fname, 'r') as f:
            routes_conf = json.load(f)
            for name, conf in routes_conf.items():
                host = conf.get('host', '(.*)')
                routes = conf.get('routes', {})
                self.hosts.append((re.compile(host), name))
                _routes = []
                for (route, route_conf) in routes.items():
                    route_conf['listen'] = self.address
                    route_conf['listen_ssl'] = self.ssl_keyfile is not None
                    if 'remote' in route_conf:
                        
                        if ROUTE_RE.match(route):
                            spec = re.compile(route)
                        else:
                            spec = re.compile("%s(.*)" % route)
                        _routes.append((route, spec, route_conf))
                
                _routes.sort()
                _routes.reverse()
                self.routes[name] = _routes
            self.hosts.sort()
            self.hosts.reverse()
