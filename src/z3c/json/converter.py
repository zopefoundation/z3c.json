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

from z3c.json import interfaces
from z3c.json import minjson
from z3c.json import exceptions


try:
    import cjson
    hasCJson = True
except ImportError:
    import logging
    logger = logging.getLogger()
    logger.log(logging.INFO,
        "Using minjson only. cjson is much faster and available at the cheese "
        "shop. easy_install python-cjson")
    hasCJson = False


class JSONReader(object):
    """JSON reader utility."""
    zope.interface.implements(interfaces.IJSONReader)

    def read(self, aString, encoding=None):
        if hasCJson:
            try:
                # the True parameter here tells cjson to make all strings 
                # unicode. This is a good idea here.
                return cjson.decode(aString, True)
            except cjson.DecodeError:
                # fall back to minjson
                pass
        # This is a fall-back position for less-well-constructed JSON
        try:
            return minjson.read(aString, encoding)
        except minjson.ReadException, e:
            raise exceptions.ResponseError(e)


class JSONWriter(object):
    """JSON writer utility."""
    zope.interface.implements(interfaces.IJSONWriter)

    def write(self, anObject):
        if hasCJson:
            try:
                return unicode(cjson.encode(anObject))
            except cjson.EncodeError:
                # fall back to minjson
                pass
        try:
            return minjson.write(anObject)
        except minjson.WriteException, e:
            raise TypeError, e


def premarshal(data):
    """Premarshal data before handing it to JSON writer for marshalling

    The initial purpose of this function is to remove security proxies
    without resorting to removeSecurityProxy. This way, we can avoid
    inadvertently providing access to data that should be protected.
    """
    premarshaller = interfaces.IJSONRPCPremarshaller(data, alternate=None)
    if premarshaller is not None:
        return premarshaller()
    return data


class PreMarshallerBase(object):
    """Abstract base class for pre-marshallers."""
    zope.interface.implements(interfaces.IJSONRPCPremarshaller)

    def __init__(self, data):
        self.data = data

    def __call__(self):
        raise Exception, "Not implemented"


class DictPreMarshaller(PreMarshallerBase):
    """Pre-marshaller for dicts"""

    def __call__(self):
        return dict([(premarshal(k), premarshal(v))
                     for (k, v) in self.data.items()])


class ListPreMarshaller(PreMarshallerBase):
    """Pre-marshaller for list"""

    def __call__(self):
        return map(premarshal, self.data)

