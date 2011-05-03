# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.
import os
import sys

from tproxy.app import Application, Script

from .config import RouteConfig


class HrouteApp(Application):

    def __init__(self):
        self.logger = None
        self.cfg = RouteConfig("%prog [OPTIONS] script_path")
        self.script = None

    def load_config(self):
        # parse console args
        parser = self.cfg.parser()
        opts, args = parser.parse_args()

        # Load conf
        try:
            for k, v in opts.__dict__.items():
                if v is None:
                    continue
                self.cfg.set(k.lower(), v)
        except Exception, e:
            sys.stderr.write("config error: %s\n" % str(e))
            os._exit(1)

        spooldir = self.cfg.spooldir
        if not spooldir and not os.path.exists('/var/spool/hroute'):
            sys.stderr.write("spool directory '/var/spool/hroute'"
                    "doesn't exist\n")
            os._exit(1)

        # setup script
        script_uri = "hroute.proxy:Route" 
        self.cfg.default_name = "hroute"
        self.script = Script(script_uri, cfg=self.cfg)
        sys.path.insert(0, os.getcwd())


def run():
    return HrouteApp().run()

