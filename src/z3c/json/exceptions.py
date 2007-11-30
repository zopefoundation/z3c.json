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


class Error(Exception):
    """Base class for client errors."""
    def __str__(self):
        return repr(self)


class ProtocolError(Error):
    """Indicates an HTTP protocol error.

    Indicates an HTTP-level protocol error.  This is raised by the HTTP
    transport layer, if the server returns an error code other than 200
    (OK).

    @param url The target URL.
    @param errcode The HTTP error code.
    @param errmsg The HTTP error message.
    @param headers The HTTP header dictionary.

    """
    def __init__(self, url, errcode, errmsg, headers):
        Error.__init__(self)
        self.url = url
        self.errcode = errcode
        self.errmsg = errmsg
        self.headers = headers
    def __repr__(self):
        return (
            "<ProtocolError for %s: %s %s>" %
            (self.url, self.errcode, self.errmsg)
            )


class ResponseError(ValueError):
    """Indicates a broken response package.

    Indicates a broken JSON-RPC response package.  This exception is
    raised by the unmarshalling layer, if the JSON-RPC response is
    malformed.
    
    """
    pass


# TODO: implement this option if we implement __jsonclass__, ri
#class Fault(Error):
#    """Indicates an JSON-RPC fault package.
#
#    Indicates an JSON-RPC fault response package.  This exception is
#    raised by the unmarshalling layer, if the JSON-RPC response contains
#    a fault string.  This exception can also used as a class, to
#    generate a fault JSON-RPC message.
#
#    @param faultCode The JSON-RPC fault code.
#    @param faultString The JSON-RPC fault string.
#
#    """
#    def __init__(self, faultCode, faultString, **extra):
#        Error.__init__(self)
#        self.faultCode = faultCode
#        self.faultString = faultString
#    def __repr__(self):
#        return (
#            "<Fault %s: %s>" %
#            (self.faultCode, repr(self.faultString))
#            )
