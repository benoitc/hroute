hroute
------

simple HTTP proxy based on `tproxy <http://github.com/benoitc/tproxy>`_. 

Features
++++++++

- location rewriting
- links rewriting to handle proxy / paths
- simple configuration


Usage:
------

Create a configuration file in /var/spool/hroute (default path) or any
folder you want::

    {
        "all": {
            "routes": {
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

            }
        }
    }


then launch hroute::

    $ hroute -s /var/spool/hroute -w 3

and go on `http://127.0.0.1:5000/gunicorn <http://127.0.0.1:5000/gunicorn>`_. You should see the gunicorn.org website.


More features soon.
