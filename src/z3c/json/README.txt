======
README
======

We can use the `JSONReader` and `JSONWriter` if we need to convert a data
structure to or from JSON syntax -- in other words a EcmaScript mapping
object. Let's check the utilities:

  >>> import zope.component
  >>> from z3c.json import interfaces
  >>> from z3c.json import testing
  >>> testing.setUpJSONConverter()


`JSONWriter` Utility
--------------------

  >>> jsonWriter = zope.component.getUtility(interfaces.IJSONWriter)
  >>> jsonWriter
  <z3c.json.converter.JSONWriter object at ...>

Read some data:

  >>> input = {u'a': ['fred', 7],
  ...          u'b':['mary', 1.234]}
  >>> jsonStr = jsonWriter.write(input)
  >>> jsonStr
  u'{"a":["fred",7],"b":["mary",1.234]}'


`JSONReader` Utility
--------------------

  >>> jsonReader = zope.component.getUtility(interfaces.IJSONReader)
  >>> jsonReader
  <z3c.json.converter.JSONReader object at ...>

Convert the data back to python:

  >>> output = jsonReader.read(jsonStr)
  >>> output
  {u'a': [u'fred', 7], u'b': [u'mary', 1.234]}

  >>> input == output
  True
