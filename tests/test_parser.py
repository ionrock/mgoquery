"""
Test our parsing and output.

One thing to note is that MgoQuery is not doing anything regarding
converting types. That is the responsibility of the caller to do so or
extend the Query class to do it.
"""

from mgoquery import Parser, Query


class TestParser(object):

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
