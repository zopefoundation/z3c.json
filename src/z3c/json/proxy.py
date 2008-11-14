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

import string
import urllib
import httplib
import copy
import base64
import types
import logging
import socket

import zope.component
from z3c.json import interfaces
from z3c.json.exceptions import ProtocolError
from z3c.json.exceptions import ResponseError

from z3c.json.transport import Transport
from z3c.json.transport import SafeTransport

logger = logging.getLogger(__name__)
JSON_RPC_VERSION = '2.0'


class _Method(object):

    def __init__(self, call, name, jsonId, jsonVersion):
        self.call = call
        self.name = name
        self.jsonId = jsonId
        self.jsonVersion = jsonVersion

    def __call__(self, *args, **kwargs):
        request = {}
        # add our version
        if self.jsonVersion == '1.0':
            pass
        elif self.jsonVersion == '1.1':
            request['version'] = self.jsonVersion
        else:
            request['jsonrpc'] = self.jsonVersion
        request['method'] = self.name

        if self.jsonVersion in ['1.0', '1.1']:
            if len(kwargs) > 0:
                params = copy.copy(kwargs)
                index = 0
                for arg in args:
                    params[str(index)] = arg
                    index += 1
            elif len(args) > 0:
                params = args
            else:
                params = []
        else:
            # There is not support for postional and named parameters in one 
            # call. We propably will add support for this within a extension
            # in a later version. Till then, we will raise an exception if
            # we will get both paramters.
            if len(args) > 0 and len(kwargs) > 0:
                raise ValueError('Mixing positional and named parameters in one call is not possible')
            if len(args) > 0:
                params = args
            elif len(kwargs) > 0:
                params = kwargs
            else:
                params = []

        # set params and write json
        request['params'] = params
        # add our json id
        request['id'] = self.jsonId
        json = zope.component.getUtility(interfaces.IJSONWriter)
        data = json.write(request)
        try:
            return self.call(data)
        except socket.error, msg:
            raise ResponseError("JSONRPC server connection error.")

    def __getattr__(self, name):
        return _Method(self.call, "%s.%s" % (self.name, name), self.jsonId,
            self.jsonVersion)


class JSONRPCProxy(object):
    """JSON-RPC server proxy."""

    def __init__(self, uri, transport=None, encoding=None,
                 verbose=None, jsonId=None, jsonVersion=JSON_RPC_VERSION):
        utype, uri = urllib.splittype(uri)
        if utype not in ("http", "https"):
            raise IOError, "Unsupported JSONRPC protocol"
        self.__host, self.__handler = urllib.splithost(uri)
        if not self.__handler:
            self.__handler = ""

        if transport is None:
            if utype == "https":
                transport = SafeTransport()
            else:
                transport = Transport()
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.jsonId = jsonId or u'jsonrpc'
        self.jsonVersion = jsonVersion or JSON_RPC_VERSION
        self.error = None

    def __request(self, request):
        """call a method on the remote server.

        This will raise a ResponseError or return the JSON result dict
        """
        # apply encoding if any
        if self.__encoding:
            request = request.encode(self.__encoding)
        # start the call
        try:
            response = self.__transport.request(self.__host, self.__handler,
                request, verbose=self.__verbose)
            self.error = None
        except ResponseError, e:
            # catch error message
            self.error = unicode(str(e), 'utf-8')
            raise

        if isinstance(response, int):
            # that's just a status code response with no result
            logger.error('Received status code %s' % response)
        elif len(response) == 3:
            # that's a valid response format
            if self.jsonId is not None and \
                (self.jsonId != response.get('id')):
                # different request id returned
                raise ResponseError("Invalid request id returned")
            if response.get('error'):
                # error mesage in response
                self.error = response['error']
                raise ResponseError("Check proxy.error for error message")
            else:
                # only return the result if everything is fine
                return response['result']

        return response

    def __getattr__(self, name):
        """This let us call methods on remote server."""
        return _Method(self.__request, name, self.jsonId, self.jsonVersion)

    def __repr__(self):
        return ("<JSONProxy for %s%s>" % (self.__host, self.__handler))

    __str__ = __repr__
