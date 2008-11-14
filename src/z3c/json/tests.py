# -*- coding: utf-8 -*-
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

import unittest
import BaseHTTPServer
import random
import threading
import urllib
import cgi
import pprint

import zope.component
from zope.testing import doctest
from zope.testing.doctestunit import DocFileSuite

from z3c.json import minjson as json
from z3c.json.minjson import ReadException
from z3c.json.minjson import WriteException

from z3c.json.interfaces import IJSONWriter, IJSONReader
from z3c.json.converter import JSONWriter, JSONReader
from z3c.json.exceptions import ResponseError, ProtocolError

from z3c.json.proxy import JSONRPCProxy


def spaceless(aString):
    return aString.replace(' ','')


class JSONTests(unittest.TestCase):

    def testReadString(self):
        s = u"'hello'"
        self.assertEqual(json.read(s) ,'hello')

    def testWriteString(self):
        s = 'hello'
        self.assertEqual(json.write(s), '"hello"')

    def testReadInt(self):
        s = u"1"
        self.assertEqual(json.read(s), 1)

    def testWriteInt(self):
        s = 1
        self.assertEqual(json.write(s), "1")

    def testReadLong(self):
        s = u"999999999999999999999"
        self.assertEqual(json.read(s), 999999999999999999999)

    def testWriteShortLong(self):
        s = 1L
        self.assertEqual(json.write(s), "1")

    def testWriteLongLong(self):
        s = 999999999999999999999L
        self.assertEqual(json.write(s), "999999999999999999999")

    def testReadNegInt(self):
        s = u"-1"
        assert json.read(s) == -1

    def testWriteNegInt(self):
        s = -1
        assert json.write(s) == '-1'

    def testReadFloat(self):
        s = u"1.334"
        assert json.read(s) == 1.334

    def testReadEFloat1(self):
        s = u"1.334E2"
        assert json.read(s) == 133.4

    def testReadEFloat2(self):
        s = u"1.334E-02"
        assert json.read(s) == 0.01334

    def testReadeFloat1(self):
        s = u"1.334e2"
        assert json.read(s) == 133.4

    def testReadeFloat2(self):
        s = u"1.334e-02"
        assert json.read(s) == 0.01334

    def testWriteFloat(self):
        s = 1.334
        assert json.write(s) == "1.334"

    def testWriteDecimal(self):
        try:
            from decimal import Decimal
            s = Decimal('1.33')
            assert json.write(s) == "1.33"
        except ImportError:
            pass

    def testReadNegFloat(self):
        s = u"-1.334"
        assert json.read(s) == -1.334

    def testWriteNegFloat(self):
        s = -1.334
        assert json.write(s) == "-1.334"

    def testReadEmptyDict(self):
        s = u"{}"
        assert json.read(s) == {}

    def testWriteEmptyList(self):
        s = []
        assert json.write(s) == "[]"

    def testWriteEmptyTuple(self):
        s = ()
        assert json.write(s) == "[]"

    def testReadEmptyList(self):
        s = u"[]"
        assert json.read(s) == []

    def testWriteEmptyDict(self):
        s = {}
        assert json.write(s) == '{}'

    def testReadTrue(self):
        s = u"true"
        assert json.read(s) == True

    def testWriteTrue(self):
        s = True
        assert json.write(s) == "true"

    def testReadStringTrue(self):
        s = u'"true"'
        assert json.read(s) == 'true'

    def testWriteStringTrue(self):
        s = "True"
        assert json.write(s) == '"True"'

    def testReadStringNull(self):
        s = u'"null"'
        assert json.read(s) == 'null'

    def testWriteStringNone(self):
        s = "None"
        assert json.write(s) == '"None"'

    def testReadFalse(self):
        s = u"false"
        assert json.read(s) == False

    def testWriteFalse(self):
        s = False
        assert json.write(s) == 'false'

    def testReadNull(self):
        s = u"null"
        assert json.read(s) == None

    def testWriteNone(self):
        s = None
        assert json.write(s) == "null"

    def testReadDictOfLists(self):
        s = u"{'a':[],'b':[]}"
        assert json.read(s) == {'a':[],'b':[]}

    def testReadDictOfListsWithSpaces(self):
        s = u"{  'a' :    [],  'b'  : []  }    "
        assert json.read(s) == {'a':[],'b':[]}

    def testWriteDictOfLists(self):
        s = {'a':[],'b':[]}
        assert spaceless(json.write(s)) == '{"a":[],"b":[]}'

    def testWriteDictOfTuples(self):
        s = {'a':(),'b':()}
        assert spaceless(json.write(s)) == '{"a":[],"b":[]}'

    def testWriteDictWithNonemptyTuples(self):
        s = {'a':('fred',7),'b':('mary',1.234)}
        w = json.write(s)
        assert spaceless(w) == '{"a":["fred",7],"b":["mary",1.234]}'

    def testWriteVirtualTuple(self):
        s = 4,4,5,6
        w = json.write(s)
        assert spaceless(w) == '[4,4,5,6]'

    def testReadListOfDicts(self):
        s = u"[{},{}]"
        assert json.read(s) == [{},{}]

    def testReadListOfDictsWithSpaces(self):
        s = u" [ {    } ,{   \n} ]   "
        assert json.read(s) == [{},{}]

    def testWriteListOfDicts(self):
        s = [{},{}]
        assert spaceless(json.write(s)) == "[{},{}]"

    def testWriteTupleOfDicts(self):
        s = ({},{})
        assert spaceless(json.write(s)) == "[{},{}]"

    def testReadListOfStrings(self):
        s = u"['a','b','c']"
        assert json.read(s) == ['a','b','c']

    def testReadListOfStringsWithSpaces(self):
        s = u" ['a'    ,'b'  ,\n  'c']  "
        assert json.read(s) == ['a','b','c']

    def testReadStringWithWhiteSpace(self):
        s = ur"'hello \tworld'"
        assert json.read(s) == 'hello \tworld'

    def testWriteMixedList(self):
        o = ['OIL',34,199L,38.5]
        assert spaceless(json.write(o)) == '["OIL",34,199,38.5]'

    def testWriteMixedTuple(self):
        o = ('OIL',34,199L,38.5)
        assert spaceless(json.write(o)) == '["OIL",34,199,38.5]'

    def testWriteStringWithWhiteSpace(self):
        s = 'hello \tworld'
        assert json.write(s) == r'"hello \tworld"'

    def testWriteListofStringsWithApostrophes(self):
        s = ["hasn't","don't","isn't",True,"won't"]
        w = json.write(s)
        assert spaceless(w) == '["hasn\'t","don\'t","isn\'t",true,"won\'t"]'

    def testWriteTupleofStringsWithApostrophes(self):
        s = ("hasn't","don't","isn't",True,"won't")
        w = json.write(s)
        assert spaceless(w) == '["hasn\'t","don\'t","isn\'t",true,"won\'t"]'

    def testWriteListofStringsWithRandomQuoting(self):
        s = ["hasn't","do\"n't","isn't",True,"wo\"n't"]
        w = json.write(s)
        assert "true" in w

    def testWriteStringWithDoubleQuote(self):
        s = "do\"nt"
        w = json.write(s)
        assert w == '"do\\\"nt"'

    def testReadDictWithSlashStarComments(self):
        s = """
        {'a':false,  /*don't want b
            b:true, */
        'c':true
        }
        """
        assert json.read(s) == {'a':False,'c':True}

    def testReadDictWithTwoSlashStarComments(self):
        s = """
        {'a':false,  /*don't want b
            b:true, */
        'c':true,
        'd':false,  /*don;t want e
            e:true, */
        'f':true
        }
        """
        assert json.read(s) == {'a':False,'c':True, 'd':False,'f':True}

    def testReadDictWithDoubleSlashComments(self):
        s = """
        {'a':false,
          //  b:true, don't want b
        'c':true
        }
        """
        assert json.read(s) == {'a':False,'c':True}

    def testReadStringWithEscapedSingleQuote(self):
        s = '"don\'t tread on me."'
        assert json.read(s) == "don't tread on me."

    def testWriteStringWithEscapedDoubleQuote(self):
        s = 'he said, \"hi.'
        t = json.write(s)
        assert json.write(s) == '"he said, \\\"hi."'

    def testReadStringWithEscapedDoubleQuote(self):
        s = r'"She said, \"Hi.\""'
        assert json.read(s) == 'She said, "Hi."'

    def testReadStringWithNewLine(self):
        s = r'"She said, \"Hi,\"\n to which he did not reply."'
        assert json.read(s) == 'She said, "Hi,"\n to which he did not reply.'

    def testReadNewLine(self):
        s = r'"\n"'
        assert json.read(s) == '\n'

    def testWriteNewLine(self):
        s = u'\n'
        assert json.write(s) == r'"\n"'

    def testWriteSimpleUnicode(self):
        s = u'hello'
        assert json.write(s) == '"hello"'

    def testReadBackSlashuUnicode(self):
        s = u'"\u0066"'
        assert json.read(s) == 'f'

    def testReadBackSlashuUnicodeInDictKey(self):
        s = u'{"\u0066ather":34}'
        assert json.read(s) == {'father':34}

    def testReadDictKeyWithBackSlash(self):
        s = u'{"mo\\use":22}'
        self.assertEqual(json.read(s) , {r'mo\use':22})

    def testWriteDictKeyWithBackSlash(self):
        s = {"mo\\use":22}
        self.assertEqual(json.write(s) , r'{"mo\\use":22}')

    def testWriteListOfBackSlashuUnicodeStrings(self):
        s = [u'\u20ac',u'\u20ac',u'\u20ac']
        self.assertEqual(spaceless(json.write(s)) ,u'["\u20ac","\u20ac","\u20ac"]')

    def testWriteUnicodeCharacter(self):
        s = json.write(u'\u1001', 'ascii')
        self.assertEqual(u'"\u1001"', s)

    def testWriteUnicodeCharacter1(self):
        s = json.write(u'\u1001', 'ascii',outputEncoding='ascii')
        self.assertEqual(r'"\u1001"', s)

    def testWriteHexUnicode(self):
        s = unicode('\xff\xfe\xbf\x00Q\x00u\x00\xe9\x00 \x00p\x00a\x00s\x00a\x00?\x00','utf-16')
        p = json.write(s, 'latin-1', outputEncoding="latin-1")
        self.assertEqual(unicode(p,'latin-1'), u'"¿Qué pasa?"')

    def testWriteHexUnicode1(self):
        s = unicode('\xff\xfe\xbf\x00Q\x00u\x00\xe9\x00 \x00p\x00a\x00s\x00a\x00?\x00','utf-16')
        p = json.write(s, 'latin-1')
        self.assertEqual(p, u'"¿Qué pasa?"')

    def testWriteDosPath(self):
        s = 'c:\\windows\\system'
        assert json.write(s) == r'"c:\\windows\\system"'

    def testWriteDosPathInList(self):
        s = ['c:\windows\system','c:\\windows\\system',r'c:\windows\system']
        self.assertEqual(json.write(s) , r'["c:\\windows\\system","c:\\windows\\system","c:\\windows\\system"]')


    def readImportExploit(self):
        s = ur"\u000aimport('os').listdir('.')"
        json.read(s)

    def testImportExploit(self):
        self.assertRaises(ReadException, self.readImportExploit)

    def readClassExploit(self):
        s = ur'''"__main__".__class__.__subclasses__()'''
        json.read(s)

    def testReadClassExploit(self):
        self.assertRaises(ReadException, self.readClassExploit)

    def readBadJson(self):
        s = "'DOS'*30"
        json.read(s)

    def testReadBadJson(self):
        self.assertRaises(ReadException, self.readBadJson)

    def readUBadJson(self):
        s = ur"\u0027DOS\u0027*30"
        json.read(s)

    def testReadUBadJson(self):
        self.assertRaises(ReadException, self.readUBadJson)

    def testReadEncodedUnicode(self):
        obj = "'La Peña'"
        r = json.read(obj, 'utf-8')
        self.assertEqual(r, unicode('La Peña','utf-8'))

    def testUnicodeFromNonUnicode(self):
        obj = "'\u20ac'"
        r = json.read(obj)
        self.assertEqual(r, u'\u20ac')

    def testUnicodeInObjectFromNonUnicode(self):
        obj = "['\u20ac', '\u20acCESS', 'my\u20ACCESS']"
        r = json.read(obj)
        self.assertEqual(r, [u'\u20AC', u'\u20acCESS', u'my\u20acCESS'])

    def testWriteWithEncoding(self):
        obj = u'La Peña'
        r = json.write(obj,'latin-1',outputEncoding='latin-1')
        self.assertEqual(unicode(r,'latin-1'), u'"La Peña"')

    def testWriteWithEncodingBaseCases(self):
        #input_uni =  u"'Ă�rvĂ­ztĹąrĹ� tĂźkĂśrfĂşrĂłgĂŠp'"
        input_uni = u'\xc1rv\xedzt\u0171r\u0151 t\xfck\xf6rf\xfar\xf3g\xe9p'
        #print "input_uni is %s" % input_uni.encode('latin2')
        # the result supposes doUxxxx = False
        good_result = u'"\xc1rv\xedzt\u0171r\u0151 t\xfck\xf6rf\xfar\xf3g\xe9p"'

        # from utf8
        obj = input_uni.encode('utf-8')
        r = json.write(obj, 'utf-8',outputEncoding='utf-8')
        self.assertEqual(unicode(r,'utf-8'), good_result)

        # from unicode
        obj = input_uni
        r = json.write(obj, outputEncoding='utf-8')
        self.assertEqual(unicode(r,'utf-8'), good_result)

        # from latin2
        obj = input_uni.encode('latin2')
        r = json.write(obj, 'latin2', outputEncoding='latin2')
        self.assertEqual(unicode(r,'latin2'), good_result)

        # from unicode, encoding is ignored
        obj = input_uni
        r = json.write(obj, 'latin2', outputEncoding='latin2')
        self.assertEqual(unicode(r,'latin2'), good_result)

        # same with composite types, uni
        good_composite_result = \
        u'["\xc1rv\xedzt\u0171r\u0151 t\xfck\xf6rf\xfar\xf3g\xe9p","\xc1rv\xedzt\u0171r\u0151 t\xfck\xf6rf\xfar\xf3g\xe9p"]'
        #print "Good composite result = %s" % good_composite_result.encode('latin2')
        obj = [input_uni, input_uni]
        r = json.write(obj, outputEncoding='utf-8')
        #print "r is %s, length is %s." % (r, len(r))
        self.assertEqual(unicode(r,'utf-8'), good_composite_result)

        # same with composite types, utf-8
        obj = [input_uni.encode('utf-8'), input_uni.encode('utf-8')]
        r = json.write(obj, 'utf-8')
        # print unicode(r,'utf-8'), good_composite_result
        #self.assertEqual(unicode(r,'utf-8'), good_composite_result)

        # same with composite types, latin2
        obj = [input_uni.encode('latin2'), input_uni.encode('latin2')]
        r = json.write(obj, 'latin2')
        #cannot assertEqual here, but the printed representation should be readable
        #self.assertEqual(unicode(r,'latin2'), good_composite_result)

        # same with composite types, mixed utf-8 with unicode
        obj = [input_uni, input_uni.encode('utf-8')]
        r = json.write(obj, 'utf-8')
        #cannot assertEqual here, but the printed representation should be readable
        #self.assertEqual(unicode(r,'utf-8'), good_composite_result)

    #these tests from Koen van der Sande; just in case we really want literal
    # '\n' sent across the wire.

    def testReadSpecialEscapedChars1(self):
        test = r'"\\f"'
        self.assertEqual([ord(x) for x in json.read(test)],[92,102])

    def testReadSpecialEscapedChars2(self):
        test = r'"\\a"'
        self.assertEqual([ord(x) for x in json.read(test)],[92,97])

    def testReadSpecialEscapedChars3(self):
        test = r'"\\\\a"'
        self.assertEqual([ord(x) for x in json.read(test)],[92,92,97])

    def testReadSpecialEscapedChars4(self):
        test = r'"\\\\b"'
        self.assertEqual([ord(x) for x in json.read(test)],[92,92,98])

    def testReadSpecialEscapedChars5(self):
        test = r'"\\\n"'
        self.assertEqual([ord(x) for x in json.read(test)],[92,10])


#We'll bring up a LIVE HTTP server on localhost to be able to test
#JSONRPCProxy
#stuff taken from zc.testbrowser.tests, thanks!

class TestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def version_string(self):
        return 'BaseHTTP'

    def date_time_string(self):
        return 'Mon, 17 Sep 2007 10:05:42 GMT'

    def do_GET(self):
        #print "GET"

        if self.path.endswith('robots.txt'):
            self.send_response(404)
            self.send_header('Connection', 'close')
            return

        global next_response_body
        global next_response_status
        global next_response_reason
        global next_response_type

        if next_response_body is None:
            self.send_response(500)
            self.send_header('Connection', 'close')
            return

        self.send_response(next_response_status)
        self.send_header('Connection', 'close')
        self.send_header('Content-type', next_response_type)
        self.send_header('Content-Length', str(len(next_response_body)))
        self.end_headers()
        self.wfile.write(next_response_body)

    def do_POST(self):
        #print "POST"

        body = self.rfile.read(int(self.headers['content-length']))

        #print body

        global last_request_body
        last_request_body = body

        global next_response_body
        global next_response_status
        global next_response_reason
        global next_response_type

        self.send_response(next_response_status)
        self.send_header('Connection', 'close')
        self.send_header('Content-type', next_response_type)
        self.send_header('Content-Length', str(len(next_response_body)))
        self.end_headers()
        self.wfile.write(next_response_body)

    def log_request(self, *args, **kws):
        pass

def set_next_response(
    response_body=None,
    response_status=200, response_reason='OK',
    response_type="text/html"):

    global next_response_body
    global next_response_status
    global next_response_reason
    global next_response_type

    next_response_body = response_body
    next_response_status = response_status
    next_response_reason = response_reason
    next_response_type = response_type

def set_next_response_json(result, jsonId=None, error=None):
    jsonId = jsonId or "jsonrpc"
    wrapper = {'id': jsonId}
    wrapper['result'] = result
    wrapper['error'] = error

    json = JSONWriter()
    data = json.write(wrapper)

    set_next_response(data,
        response_type="application/x-javascript;charset=utf-8"
        )



def get_last_request():
    global last_request_body
    return last_request_body

def serve_requests(server):
    global json_test_server_stop
    while not json_test_server_stop:
        server.handle_request()
    server.server_close()

def setUpServer(test):
    global json_test_server_stop
    json_test_server_stop = False
    port = random.randint(20000,30000)
    test.TEST_PORT = port
    server = BaseHTTPServer.HTTPServer(('localhost', port), TestHandler)
    thread = threading.Thread(target=serve_requests, args=[server])
    thread.setDaemon(True)
    thread.start()
    test.web_server_thread = thread

def tearDownServer(test):
    global json_test_server_stop
    json_test_server_stop = True
    # make a request, so the last call to `handle_one_request` will return
    try:
        urllib.urlretrieve('http://localhost:%d/' % test.TEST_PORT)
    except IOError:
        pass # it's ok, server is already dead
    test.web_server_thread.join()


class JSONRPCProxyLiveTester(unittest.TestCase):
    def setUp(self):
        zope.component.provideUtility(JSONWriter(), IJSONWriter)
        zope.component.provideUtility(JSONReader(), IJSONReader)

        setUpServer(self)

    def tearDown(self):
        tearDownServer(self)

    def testSimple(self):
        proxy = JSONRPCProxy('http://localhost:%d/' % self.TEST_PORT)
        set_next_response_json(True, "jsonrpc")
        y = proxy.hello()
        self.assertEqual(y, True)

        x = get_last_request()
        self.assertEqual(x,
            """{"params":[],"jsonrpc":"2.0","method":"hello","id":"jsonrpc"}""")

        set_next_response_json(123, "jsonrpc")
        y = proxy.greeting(u'Jessy')
        self.assertEqual(y, 123)

        x = get_last_request()
        self.assertEqual(x,
            """{"params":["Jessy"],"jsonrpc":"2.0","method":"greeting","id":"jsonrpc"}""")

        set_next_response('blabla')
        try:
            y = proxy.hello()
        except ResponseError:
            pass
        else:
            self.fail("ResponseError expected")

        set_next_response('{blabla}')
        try:
            y = proxy.hello()
        except ResponseError:
            pass
        else:
            self.fail("ResponseError expected")

    dataToTest = [
        {'response_json': True,
         'call_method': 'hello',
         'assert_retval': True,
         'assert_request':
            """{"params":[],"jsonrpc":"2.0","method":"hello","id":"jsonrpc"}""",
        },
        {'response_json': 123,
         'call_method': 'greeting',
         'call_args': [u'Jessy'],
         'assert_retval': 123,
         'assert_request':
            """{"params":["Jessy"],"jsonrpc":"2.0","method":"greeting","id":"jsonrpc"}""",
        },
        {'response': 'blabla',
         'call_method': 'hello',
         'exception': ResponseError,
        },
        {'response': 'blabla',
         'response_status': 404,
         'call_method': 'hello',
         'exception': ProtocolError,
        },
    ]

    def testDataDriven(self):
        for item in self.dataToTest:
            jsonid = item.get('proxy_jsonid', None)
            transport = item.get('proxy_transport', None)
            proxy = JSONRPCProxy('http://localhost:%d/' % self.TEST_PORT,
                                 transport=transport,
                                 jsonId=jsonid)

            if 'response_json' in item:
                #set response based on JSON data
                error = item.get('response_json_error', None)
                jsonid = item.get('response_jsonid', None)
                set_next_response_json(item['response_json'],
                                       jsonid, error=error)
            else:
                #set response based on plain HTTP data
                response_status=item.get('response_status', 200)
                response_reason=item.get('response_reason', 'OK')
                response_type=item.get('response_type',"text/html")

                set_next_response(item['response'], response_status,
                    response_reason, response_type)

            args = item.get('call_args', [])
            kwargs = item.get('call_kwargs', {})
            exception = item.get('exception', None)
            method = getattr(proxy, item['call_method'])

            if exception:
                try:
                    retval = method(*args, **kwargs)
                except exception:
                    pass
                else:
                    self.fail("%s expected" % str(exception.__class__))

                if 'assert_request' in item:
                    x = get_last_request()
                    self.assertEqual(x, item['assert_request'])
            else:
                retval = method(*args, **kwargs)
                if 'assert_retval' in item:
                    self.assertEqual(retval, item['assert_retval'])
                if 'assert_request' in item:
                    x = get_last_request()
                    self.assertEqual(x, item['assert_request'])

def test_suite():
    return unittest.TestSuite((
        DocFileSuite('README.txt',
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
            ),
        unittest.makeSuite(JSONTests),
        unittest.makeSuite(JSONRPCProxyLiveTester),
        ))


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
    #unittest.TextTestRunner().run(test_suite())
