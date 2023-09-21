import pytest
from dotchain import DotChain


class TestChainClass:
    def __init__(self, prop_value='P', meth_value='M', generator_items=[1, 2, 3]):
        self.prop_value = prop_value
        self.meth_value = meth_value
        self.generator_items = generator_items

    @property
    def prop(self):
        return self.prop_value

    def meth(self):
        return self.meth_value

    def arg_meth(self, *args, **kwargs):
        return args, kwargs

    async def async_arg_meth(self, *args, **kwargs):
        return args, kwargs

    def args_meth(self, args):
        return args

    def kwargs_meth(self, kwargs):
        return kwargs

    def generator(self, items=None):
        items = self.generator_items if items is None else items
        for item in items:
            yield item

    async def async_generator(self, items=None):
        items = self.generator_items if items is None else items
        for item in items:
            yield item


class TestContext:
    @staticmethod
    def select(iterable, pred=None):
        return list(filter(pred, iterable)) or None

    @classmethod
    def select_c(cls, iterable, pred=None):
        return TestContext.select(iterable, pred=pred)

    def select_i(self, iterable, pred=None):
        return TestContext.select(iterable, pred=pred)

    @staticmethod
    def first(iterable):
        return iterable[0] if len(iterable) else None

    @classmethod
    def first_c(cls, iterable):
        return TestContext.first(iterable)

    def first_i(self, iterable):
        return TestContext.first(iterable)

    @staticmethod
    def last(iterable):
        reversed_iterable = iterable[::-1]
        return reversed_iterable[0] if len(reversed_iterable) else None

    @classmethod
    def last_c(cls, iterable):
        return TestContext.last(iterable)

    def last_i(self, iterable):
        return TestContext.last(iterable)


async def test_chaining():
    tcc = TestChainClass()

    assert DotChain(tcc).prop.Result() == tcc.prop_value

    assert DotChain(tcc).prop.Result() == tcc.prop_value
    assert await DotChain(tcc).prop == tcc.prop_value

    assert DotChain(tcc).prop.upper().Result() == tcc.prop_value.upper()
    assert await DotChain(tcc).prop.upper() == tcc.prop_value.upper()

    assert DotChain(tcc).meth().Result() == tcc.meth_value
    assert await DotChain(tcc).meth() == tcc.meth_value

    assert DotChain(tcc).meth().upper().Result() == tcc.meth_value.upper()
    assert await DotChain(tcc).meth().upper() == tcc.meth_value.upper()

    assert DotChain(tcc).arg_meth('test', bool=True).Result() == (('test',), {'bool': True})
    assert await DotChain(tcc).arg_meth('test', bool=True) == (('test',), {'bool': True})

    assert await DotChain(tcc).async_arg_meth('test', bool=True) == (('test',), {'bool': True})

    assert [o for o in DotChain(tcc).generator().Result()] == tcc.generator_items
    assert [o async for o in DotChain(tcc).generator()] == tcc.generator_items
    assert list(DotChain(tcc).generator([7, 8, 9]).Result()) == [7, 8, 9]

    assert [o async for o in DotChain(tcc).async_generator()] == tcc.generator_items
    assert list([o async for o in DotChain(tcc).async_generator([7, 8, 9])]) == [7, 8, 9]


async def test_piping():
    iterable = [0, 1, 2, 3]

    # Set context and Pipe with constructor.
    assert DotChain(iterable, context=TestContext, pipe=True).select(lambda i: i == 1).first().Result() == 1
    assert await DotChain(iterable, context=TestContext, pipe=True).select(lambda i: i == 1).first() == 1

    # Test each context method - class method, static method, instance method.
    assert DotChain(iterable, context=[TestContext, TestContext()], pipe=True). \
               select(lambda i: i == 1). \
               select_i(lambda i: i == 1). \
               select_c(lambda i: i == 1). \
               first().Result() == 1

    # Set context and Pipe with methods/properties.
    assert DotChain(iterable).With(TestContext).Pipe.select(lambda i: i == 1).first().Result() == 1
    assert await DotChain(iterable).With(TestContext).Pipe.select(lambda i: i == 1).first() == 1

    # Switch between chaining and piping.
    assert DotChain(iterable).With(TestContext).Pipe.select().last().str().Chain.rjust(2, '_').Result() == '_3'
    assert await DotChain(iterable).With(TestContext).Pipe.select().last().str().Chain.rjust(2, '_') == '_3'

    assert DotChain('0,1,2,3').With(TestContext).split(',').Pipe.first().str().Chain.rjust(2, '_').Result() == '_0'
    assert await DotChain('0,1,2,3').With(TestContext).split(',').Pipe.first().str().Chain.rjust(2, '_') == '_0'

    # Custom callables.
    assert DotChain(iterable).Pipe. \
               Call(lambda items: TestContext.select(items)). \
               Call(lambda items: TestContext.last(items)). \
               str().Chain.rjust(2, '_').Result() == '_3'
    assert await DotChain(iterable).Pipe. \
        Call(lambda items: TestContext.select(items)). \
        Call(lambda items: TestContext.last(items)). \
        str().Chain.rjust(2, '_') == '_3'

    # Callable from contexts.
    assert DotChain(iterable).With(TestContext, {'custom': lambda items: items[0]}). \
               Pipe.custom().str().Chain.rjust(2, '_').Result() == '_0'
    assert await DotChain(iterable).With(TestContext, {'custom': lambda items: items[0]}). \
        Pipe.custom().str().Chain.rjust(2, '_') == '_0'

    # Missing attributes.
    with pytest.raises(AttributeError) as ex:
        DotChain(iterable).With(TestContext).Pipe.select().last().str().Chain.rjust(2, '_').Nope.Result() == '_3'
    assert "cannot find attribute \'Nope\'" in str(ex)
    with pytest.raises(AttributeError) as ex:
        await DotChain(iterable).With(TestContext).Pipe.select().last().str().Chain.rjust(2, '_').Nope == '_3'
    assert "cannot find attribute \'Nope\'" in str(ex)

    tcc = TestChainClass()
    assert (DotChain(tcc).With(TestContext).arg_meth('test', bool=True).Pipe.select().Result() ==
            [('test',), {'bool': True}])
    assert await DotChain(tcc).With(TestContext).arg_meth('test', bool=True).Pipe.select() == \
           [('test',), {'bool': True}]

    assert DotChain(tcc).generator().Pipe.list().Result() == tcc.generator_items
    assert await DotChain(tcc).generator().Pipe.list() == tcc.generator_items

    tcc2 = TestChainClass(tcc, tcc)
    assert DotChain(tcc2).Pipe.prop.arg_meth().Result() == ((tcc2,), {})
    assert await DotChain(tcc2).Pipe.prop.arg_meth() == ((tcc2,), {})

    assert DotChain(tcc2).args_meth(tcc).Pipe.args_meth().Result() == tcc
    assert await DotChain(tcc2).args_meth(tcc).Pipe.args_meth() == tcc
