hroute
------

simple HTTP proxy based on `tproxy <http://github.com/benoitc/tproxy>`_. 

Features
++++++++

- location rewriting
- links rewriting to handle proxy / paths
- simple configuration
- vhosts support
- logging (coming)
- authentification (coming)


Requirements
------------

- `Python <http://python.org>`_ 2.6 and sup (Python 3 not suppported yet)
- `gevent <http://gevent.org>`_ >= 0.13.4
- `setproctitle <http://code.google.com/p/py-setproctitle/>`_ >= 1.1.2
- `tproxy  <http://github.com/benoitc/http-parser>`_ >= 0.5.2
- `http-parser <http://github.com/benoitc/http-parser>`_ >= 0.3.3
- `lxml <http://lxml.de>`_ 

Install
-------

::
    
    $ pip install -r https://github.com/downloads/benoitc/hroute/requirements.txt
    $ pip install hroute


Usage
-----

Create a configuration file named **route** in /var/spool/hroute
(default path) or any folder you want, for example in /tmp, put the
following configuration::

    {
        "all": {
            "routes": {
                "/": {
                    "remote": "benoitc.io:80",
                    "rewrite_response": true
                },
                "/local": {
                    "remote": "127.0.0.1:8000"
                },
                "/google": {
                    "remote": "google.com:80"
                },
                "/gunicorn": {
                    "remote": "gunicorn.org:80",
                    "rewrite_response": true
                },
                "/googles": {
                    "remote": "encrypted.google.com:443",
                    "ssl": true,
                    "rewrite_response": true
                }
            }
        }
    }


then launch hroute::

    $ hroute -s /tmp -w 3

and go on `http://127.0.0.1:5000/gunicorn
<http://127.0.0.1:5000/gunicorn>`_. You should see the gunicorn.org
website.


More features soon.
