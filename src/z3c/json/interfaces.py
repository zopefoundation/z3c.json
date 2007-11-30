##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id:$
"""
__docformat__ = "reStructuredText"

import zope.interface


class IJSONReader(zope.interface.Interface):
    """JSON reader."""

    def read(aString):
        """read and interpret a string in JSON as python"""
        

class IJSONWriter(zope.interface.Interface):
    """JSON writer."""

    def write(anObject, encoding=None):
        """return a JSON unicode string representation of a python object
           Encode if encoding is provided.
        """
    

class IJSONRPCPremarshaller(zope.interface.Interface):
    """Premarshaller to remove security proxies"""

    def __call__():
        """return the object without proxies"""
