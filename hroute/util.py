# -*- coding: utf-8 -
#
# This file is part of hroute released under the MIT license. 
# See the NOTICE for more information.

import os
import posixpath

def normalize(prefix, link):
    # anchors
    if link.startswith("#"):
        return link

    path = posixpath.normpath(os.path.join(prefix, link))
    return  path
