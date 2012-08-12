MgoQuery (MongoDB Query Parser)
===============================

A simple query language that returns a valid MongoDB query.

MongoDB provides a flexible query model that is powerful, yet verbose
at times. MgoQuery provides a simple query langauge to create a
concise, search-like syntax for constructing MongoDB queries.

Goals
-----

 1. Provide a safe and limited interface for querying MongoDB.
 2. Provide a query language that is URL friendly


Query Syntax
------------

The MgoQuery syntax is inspired by tools such as Xapian, Lucene and
GMail's advance query search.

Here is an example of the basic format: ::

  "x>3, x<5" | "y>10, z:True"

Which translates to: ::

  {'$or': [{'$and': [{'x': {'$gte': 3}},
                     {'x': {'$lte': 5}}]},
           {'$and': [{'y': {'$gte': 10}},
                     {'z': True}]}]}


Spaces are optional which means the above query could be rewritten as: ::

  "x>3,x<5"|"y>10,z:True"
  "x>3, x<5" | "y>10, z:True"

Expressions
~~~~~~~~~~~

An expression defines a single requirement for a single key in a
MongoDB query. For example ::

  {'x': 1}

An expression in a MgoQuery is as follows: ::

  $key <-> operator <-> $value

The operators are as follows:

  equals = ":"
  greater than or equal to >= ">"
  less than or equal to <= "<"

It should be noted that we only use greater/less than or equal to as
the theory is it will be easier for users to understand the value they
use will be included in the results.

Here are some examples: ::

  x:3     => {'x': '3'}
  foo > 4 => {'foo': {'$gte': '4'}}
  y < x   => {'y': {'$lte': 'x'}}

One thing to note in the above examples is that the values are all
strings. I will explain how to help the parser know when you want to
use different types in the parsed output. 

Expressions can be combined in order to create more complex
expressions. There are two ways to combine expressions, grouping and
combination operators.

Combination Operators
~~~~~~~~~~~~~~~~~~~

Similar to the operators in expressions, combination operators act
upon two expressions. ::

  expression <-> operator <-> expression

Here are two examples using the two combination operators: ::

  x:1 , y:2 => {'$and': [{'x': '1'}, {'y': '2'}]}
  x:1 | y:2 => {'$or': [{'x': '1'}, {'y': '2'}]}
  

The "," acts as an AND operator meaning both expressions would need to
match in the document for it to be returned. 

The "|" acts as an OR operator such that either expression can match
in order for the document to be returned. 

I should be noted that you may only use combination operator at a
time. There is no precendence that takes place in order to clarify
how the expression should be applied. For example: ::

  x:1, y:2 | foo:bar

There is no way for the parser to know whether you intended the 'y:2'
expression to be compared first to the 'x:1' with AND or with the
'foo:bar' using OR.

It is possible to use different combination operators by using groups.

Groups
~~~~~~

Groups allow you to use more than one combination operator in a
query. Here is the format for a group: ::

  "expression [<-> operator]"

Quotes are used to wrap the expressions and the combination operator
such that you can use more than one. Here is a more complex example to
see how this works: ::

  "x>1, x<5" | "y>2, x:None"

In this example the groups are surrounded in the quotes and use the
AND operator. Both groups are then used in an OR operation. In english
the example would read as: 

  Select all documents if:
    The key 'x' is greater than or equal to 1 AND
    The key 'x' is less than or equal to 5
  OR
    The key 'y' is greater than or equal to 2 AND
    The key 'x' does not exist or is None.

Currently groups cannot be nested as we do not have the use case for
this complex of queries.


Using the Parser
================

Here is a small session showing how to use the parser in order to
construct queries: ::

  Python 2.7.1 (r271:86832, Jul 31 2011, 19:30:53) 
  [GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2335.15.00)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>> from pprint import pprint
  >>> from mgoquery import Parser
  >>> p = Parser()
  >>> result = p.parse('x > 5, y < 3')
  >>> print result
  {'$and': [{'x': {'$gte': '5'}}, {'y': {'$lte': '3'}}]}

Converting Values in Queries
----------------------------

As you can see from the examples, the parser default does not make an
effort to understand the type of value for each expression. In order
to convert the value to the correct type you can pass a conversion
function to the Parser constructor. 

Here is a simple session using the same example from above: ::

  >>> p = Parser(conversion=lambda key, value: int(value))
  >>> print(p.parse('x:1, y:2'))
  {'$and': [{'x': 1}, {'y': 2}]}

The conversion function should take two arguments, a "key" and
"value". The key is the name of the key used by the documents you want
to query. As MongoDB doesn't support forcing a type on a specific key
in a collection of documents, we use the name of the key to provide a
suggestion as to what type to use. 

Here is an example using a potential date parsing function: ::

  from mylibs import parse_date
  from mgoquery import Parser

  def value_conversion(key, value):
      if 'date' in key or 'time' in key:
          return parse_date(value)
      return value
 
  
  p = Parser(conversion=value_conversion)
  print(p.parse('startdate:2012-02-03'))
  # prints -> {'starttdate': datetime(2012, 2, 3)}

The return value of the conversion function should be the converted
value. It is also appropriate to validate the input and throw an error
if it is invalid.
