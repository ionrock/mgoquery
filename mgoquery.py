from __future__ import print_function
from pyparsing import (Word, alphanums, Suppress,
                       Optional, OneOrMore)


class Expr(object):
    def __init__(self, op, k, v, conversion=None):
        self.op = op
        self.k = k
        self.v = v
        self.conversion = conversion

    def as_dict(self):
        value = self.v
        if self.conversion:
            value = self.conversion(self.k, self.v)

        if self.op == '$eq':
            return {self.k: value}
        return {self.k: {self.op: value}}


class AndOr(object):
    def __init__(self, op, exprs):
        self.op = op
        self.exprs = exprs

    def as_dict(self):
        return {self.op: [e.as_dict() for e in self.exprs]}


class Query(object):
    def __init__(self, parse_result):
        self.parse_result = parse_result

    def as_dict(self):
        query = {}
        for part in self.parse_result:
            query.update(part.as_dict())
        return query


class Parser(object):

    def __init__(self, conversion=None):
        self._parser = self.parser()
        self._query = {}
        self.conversion = conversion

    def parser(self):
        """
        Create our grammar and parser
        """

        # Basic elements for expressions
        field = Word(alphanums + '_-')
        operator = Word(':><')
        value = Word(alphanums + '_-/:.\[]()')

        # Our expression
        expression = field + operator + value
        expression.setParseAction(self.handle_expression)

        # Grouping with AND/OR
        andor_token = Word('|,')

        # An expression list is a list of expression delimited with an
        # AND/OR token.
        expression_list = OneOrMore(expression + Optional(andor_token))
        expression_list.setParseAction(self.handle_and_or)

        # A group allows combining different AND and OR expression
        # lists.
        group = Suppress('"') + expression_list + Suppress('"')
        group_or_expression = group | expression

        # A top level AND/OR. We only support one level of
        # grouping. You can have an OR with ANDs or an AND with
        # ORs. If you want something more complicated, then you
        # probably should just construct the query yourself.
        andor = OneOrMore(group_or_expression + Optional(andor_token))
        andor.setParseAction(self.handle_and_or)

        # We can start with a top level AND/OR, expression list or a
        # group
        grammar = andor | expression_list | group
        return grammar

    def parse(self, s):
        r = self._parser.parseString(s)
        q = Query(r)
        return q.as_dict()

    def handle_expression(self, s, loc, toks):
        """
        Take the operator and move it to the front in order to make
        using the results prefix heavy.
        """
        ops = {
            '>': '$gte', '<': '$lte', ':': '$eq'
        }
        k, op, v = toks
        return [Expr(ops[op], k, v, self.conversion)]

    def handle_and_or(self, s, loc, toks):
        """
        Take the combining AND/OR token and move it to the front of
        the list in order to make the results prefix heavy.
        """
        expressions = []
        andor = None
        for t in toks:
            if t == '|':
                andor = '$or'
            elif t == ',':
                andor = '$and'
            else:
                expressions.append(t)

        if not andor:
            return toks
        return [AndOr(andor, expressions)]

if __name__ == '__main__':
    p = Parser()
    print(Query(p.parse('"x>3,x<5"|"y>10,z:True"')).as_dict())
    print(Query(p.parse('"x:3,y>8"|foo:bar')).as_dict())
