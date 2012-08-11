"""
Test our parsing and output.

One thing to note is that MgoQuery is not doing anything regarding
converting types. That is the responsibility of the caller to do so or
extend the Query class to do it.
"""
import pytest

from mgoquery import Parser, Query


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
        withspace = Query(p.parse(query)).as_dict()
        nospace = Query(p.parse(query.replace(' ', ''))).as_dict()
        assert withspace == nospace

    def test_operators(self):
        p = Parser()
        eq = Query(p.parse('x:y'))
        assert eq.as_dict() == {'x': 'y'}

        gt = Query(p.parse('x>y'))
        assert gt.as_dict() == {'x': {'$gte': 'y'}}

        lt = Query(p.parse('x<y'))
        assert lt.as_dict() == {'x': {'$lte': 'y'}}

    def test_operator_in_group(self):
        p = Parser()
        eq = Query(p.parse('"x:y"'))
        assert eq.as_dict() == {'x': 'y'}

        gt = Query(p.parse('"x>y"'))
        assert gt.as_dict() == {'x': {'$gte': 'y'}}

        lt = Query(p.parse('"x<y"'))
        assert lt.as_dict() == {'x': {'$lte': 'y'}}

    def test_no_group_or(self):
        p = Parser()
        query = Query(p.parse('"x:y|x:z"'))
        assert query.as_dict() == {'$or': [{'x': 'y'}, {'x': 'z'}]}

    def test_no_group_and(self):
        p = Parser()
        query = Query(p.parse('"x:y,a:b"'))
        assert query.as_dict() == {'$and': [{'x': 'y'}, {'a': 'b'}]}

        query = Query(p.parse('"x:y a:b"'))
        assert query.as_dict() == {'x': 'y', 'a': 'b'}

    def test_grouped_or_with_and(self):
        p = Parser()
        query = Query(p.parse('"x:y|a:b","foo:bar"'))
        assert query.as_dict() == {'$and': [{'$or': [{'x': 'y'}, {'a': 'b'}]},
                                            {'foo': 'bar'}]}

    def test_grouped_or_with_implicit_and(self):
        p = Parser()
        query = Query(p.parse('"x:y|a:b" "foo:bar"'))
        assert query.as_dict() == {'foo': 'bar',
                                   '$or': [{'x': 'y'}, {'a': 'b'}]}

    def test_grouped_and_with_or(self):
        p = Parser()
        query = Query(p.parse('"x>1,x<5" | "y>10|y:None"'))
        assert query.as_dict() == {'$or': [{'$and': [{'x': {'$gte': '1'}},
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
        return Query(self.p.parse(query))

    @pytest.mark.parametrize(('query', 'expected'), query_tests)
    def test_map(self, query, expected):
        q = self.get_query(query)
        assert q.as_dict() == expected
