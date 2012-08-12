"""
Test our parsing and output.

One thing to note is that MgoQuery is not doing anything regarding
converting types. That is the responsibility of the caller to do so or
extend the Query class to do it.
"""
import pytest

from mgoquery import Parser


class TestParser(object):

    @pytest.mark.parametrize(
        ('query',), [
            ('x : y',),
            ('x : y , a : b',),
            ('" x > y | x < z " , "a > b , a < c"',),
            ('x > y, a > b',),

            # This fails but it might be nice if we returned:
            #   {'x': 'y', 'a': 'b'}
            # Since mongo uses AND implicitly
            # ('x:y a:b',),
        ])
    def test_whitespace(self, query):
        """
        Makesure we get the same results no matter the whitespace.
        """
        p = Parser()
        withspace = p.parse(query)
        nospace = p.parse(query.replace(' ', ''))
        assert withspace == nospace

    def test_operators(self):
        p = Parser()
        eq = p.parse('x:y')
        assert eq == {'x': 'y'}

        gt = p.parse('x>y')
        assert gt == {'x': {'$gte': 'y'}}

        lt = p.parse('x<y')
        assert lt == {'x': {'$lte': 'y'}}

    def test_operator_in_group(self):
        p = Parser()
        eq = p.parse('"x:y"')
        assert eq == {'x': 'y'}

        gt = p.parse('"x>y"')
        assert gt == {'x': {'$gte': 'y'}}

        lt = p.parse('"x<y"')
        assert lt == {'x': {'$lte': 'y'}}

    def test_no_group_or(self):
        p = Parser()
        query = p.parse('"x:y|x:z"')
        assert query == {'$or': [{'x': 'y'}, {'x': 'z'}]}

    def test_no_group_and(self):
        p = Parser()
        query = p.parse('"x:y,a:b"')
        assert query == {'$and': [{'x': 'y'}, {'a': 'b'}]}

        query = p.parse('"x:y a:b"')
        assert query == {'x': 'y', 'a': 'b'}

    def test_grouped_or_with_and(self):
        p = Parser()
        query = p.parse('"x:y|a:b","foo:bar"')
        assert query == {'$and': [{'$or': [{'x': 'y'}, {'a': 'b'}]},
                                            {'foo': 'bar'}]}

    def test_grouped_or_with_implicit_and(self):
        p = Parser()
        query = p.parse('"x:y|a:b" "foo:bar"')
        assert query == {'foo': 'bar',
                                   '$or': [{'x': 'y'}, {'a': 'b'}]}

    def test_grouped_and_with_or(self):
        p = Parser()
        query = p.parse('"x>1,x<5" | "y>10|y:None"')
        assert query == {'$or': [{'$and': [{'x': {'$gte': '1'}},
                                                     {'x': {'$lte': '5'}}]},
                                           {'$or': [{'y': {'$gte': '10'}},
                                                    {'y': 'None'}]}]}


class TestParseAndValidate(object):
    """
    The parser can accept a validator callable that can be used to
    convert any values to the proper type.

    Here is an example using a set list of converter functions ::

      def format_values(k, v):
          conversion_map = {
              'start': parse_datetime,
              'end': parse_datetime,
              'size': int,
              'amount': float,
          }
          return conversion_map.get(k, lambda x: x)

    As MongoDB doesn't enforce any sort of type constraint on a
    document, we depend on the key in order to supply the correct
    conversion method.
    """

    def to_int(k, v):
        return int(v)

    p = Parser(conversion=to_int)
    query_tests = [
        ('x:1', {'x': 1}),
        ('x>1', {'x': {'$gte': 1}}),
        ('x:1|a:2', {'$or': [{'x': 1}, {'a': 2}]}),
        ('"x:1,y:2"|"foo:5,bar:6"', {'$or': [{'$and': [{'x': 1},
                                                       {'y': 2}]},
                                             {'$and': [{'foo': 5},
                                                       {'bar': 6}]}]})
    ]

    def get_query(self, query):
        return self.p.parse(query)

    @pytest.mark.parametrize(('query', 'expected'), query_tests)
    def test_map(self, query, expected):
        q = self.get_query(query)
        assert q == expected
