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

import zope.component

from z3c.json import interfaces
from z3c.json import converter


def setUpJSONConverter():
    zope.component.provideUtility(converter.JSONReader(), interfaces.IJSONReader)
    zope.component.provideUtility(converter.JSONWriter(), interfaces.IJSONWriter)
    zope.component.provideAdapter(converter.ListPreMarshaller, (list,))
    zope.component.provideAdapter(converter.ListPreMarshaller, (tuple,))
    zope.component.provideAdapter(converter.DictPreMarshaller, (dict,))
