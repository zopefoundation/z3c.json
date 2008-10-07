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
import base64
import types

import zope.component
from z3c.json import interfaces
from z3c.json.exceptions import ProtocolError
from z3c.json.exceptions import ResponseError


def getparser():
    un = Unmarshaller()
    par = Parser(un)
    return par,un


class Unmarshaller(object):
    def __init__(self):
        self.data = None

    def feed(self, data):
        if self.data is None:
            self.data = data
        else:
            self.data = self.data + data

    def close(self):
        # convert to json, reader raises ResponseError on read error
        json = zope.component.getUtility(interfaces.IJSONReader)
        return json.read(self.data)


class Parser(object):
    def __init__(self, unmarshaller):
        self._target = unmarshaller
        self.data = None

    def feed(self, data):
        if self.data is None:
            self.data = data
        else:
            self.data = self.data + data

    def close(self):
        self._target.feed(self.data)


class Transport:
    """Handles an HTTP transaction to an JSON-RPC server.

    Standard transport class for JSON-RPC over HTTP.
    You can create custom transports by subclassing this method, and
    overriding selected methods.

    Send a complete request, and parse the response.

    @param host Target host.
    @param handler Target PRC handler.
    @param request_body JSON-RPC request body.
    @param verbose Debugging flag.
    @return Parsed response.

    """

    user_agent = "z3c.jsonrpc/0.5.0"

    def request(self, host, handler, request_body, verbose=0):
        # issue JSON-RPC request

        h = self.make_connection(host)
        if verbose:
            h.set_debuglevel(1)

        self.send_request(h, handler, request_body)
        self.send_host(h, host)
        self.send_user_agent(h)
        self.send_content(h, request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(host + handler, errcode, errmsg, headers)

        self.verbose = verbose

        self.parse_response_headers(headers)

        try:
            sock = h._conn.sock
        except AttributeError:
            sock = None

        return self._parse_response(h.getfile(), sock)

    def getparser(self):
        """Get parser and unmarshaller."""
        return getparser()

    def get_host_info(self, host):
        """Get authorization info from host parameter

        Host may be a string, or a (host, x509-dict) tuple; if a string,
        it is checked for a "user:pw@host" format, and a "Basic
        Authentication" header is added if appropriate.

        @param host Host descriptor (URL or (URL, x509 info) tuple).
        @return A 3-tuple containing (actual host, extra headers,
        x509 info).  The header and x509 fields may be None.

        """
        x509 = {}
        if isinstance(host, types.TupleType):
            host, x509 = host

        auth, host = urllib.splituser(host)

        if auth:
            auth = base64.encodestring(urllib.unquote(auth))
            auth = string.join(string.split(auth), "") # get rid of whitespace
            extra_headers = [
                ("Authorization", "Basic " + auth)
                ]
        else:
            extra_headers = None

        return host, extra_headers, x509

    def make_connection(self, host):
        # create a HTTP connection object from a host descriptor
        host, extra_headers, x509 = self.get_host_info(host)
        return httplib.HTTP(host)

    def send_request(self, connection, handler, request_body):
        connection.putrequest("POST", handler)

    def send_host(self, connection, host):
        host, extra_headers, x509 = self.get_host_info(host)
        connection.putheader("Host", host)
        if extra_headers:
            if isinstance(extra_headers, dict):
                extra_headers = extra_headers.items()
            for key, value in extra_headers:
                connection.putheader(key, value)

    def send_user_agent(self, connection):
        connection.putheader("User-Agent", self.user_agent)

    def send_content(self, connection, request_body):
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(len(request_body)))
        connection.endheaders()
        if request_body:
            connection.send(request_body)

    def parse_response_headers(self, headers):
        pass

    def parse_response(self, file):
        # compatibility interface
        return self._parse_response(file, None)

    def _parse_response(self, file, sock):
        # read response from input file/socket, and parse it

        p, u = self.getparser()

        while 1:
            if sock:
                response = sock.recv(1024)
            else:
                response = file.read(1024)
            if not response:
                break
            if self.verbose:
                print "body:", repr(response)
            p.feed(response)

        file.close()
        p.close()

        return u.close()


class SafeTransport(Transport):
    """Handles an HTTPS transaction to an JSON-RPC server."""

    def make_connection(self, host):
        """Create a HTTPS connection object from a host descriptor

        host may be a string, or a (host, x509-dict) tuple

        """
        host, extra_headers, x509 = self.get_host_info(host)
        try:
            HTTPS = httplib.HTTPS
        except AttributeError:
            raise NotImplementedError(
                "your version of httplib doesn't support HTTPS"
                )
        else:
            return HTTPS(host, None, **(x509 or {}))


class BasicAuthTransport(Transport):

    def __init__(self, username=None, password=None, verbose=0):
        self.username=username
        self.password=password
        self.verbose=verbose

    def request(self, host, handler, request_body, verbose=0):
        # issue JSON-RPC request

        self.verbose = verbose

        h = httplib.HTTP(host)
        h.putrequest("POST", handler)

        # required by HTTP/1.1
        h.putheader("Host", host)

        # required by JSON-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "application/json")
        h.putheader("Content-Length", str(len(request_body)))

        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" %
                base64.encodestring("%s:%s" % (self.username, self.password)
                    ).replace("\012", ""))
        h.endheaders()

        if request_body:
            h.send(request_body)

        errcode, errmsg, headers = h.getreply()

        if errcode != 200:
            raise ProtocolError(host + handler, errcode, errmsg, headers)

        return self.parse_response(h.getfile())
