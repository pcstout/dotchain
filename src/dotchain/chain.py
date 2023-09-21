from __future__ import annotations
import typing as t
from collections.abc import Iterable
import asyncio
import builtins
import inspect
from functools import partial


class Chain:
    __slots__ = ('data', 'contexts', 'parent', 'pipe', 'generator', 'generator_is_async')

    def __init__(self, data: t.Any = None,
                 context: t.Optional[t.Any | list[t.Any]] = [],
                 parent: t.Optional[Chain] = None,
                 pipe: t.Optional[bool] = False):
        self.data = data
        self.parent = parent
        self.pipe = pipe
        self.generator = None
        self.generator_is_async = None
        self.contexts = []
        self.set_contexts(*context if isinstance(context, Iterable) else [context])

    def __await__(self):
        return self.__result_async__().__await__()

    def __aiter__(self):
        self.generator = None
        self.generator_is_async = None
        return self

    async def __anext__(self):
        if self.generator is None:
            self.generator = await self.__result_async__()
            self.generator_is_async = inspect.isasyncgen(self.generator)

        if self.generator_is_async:
            return await self.generator.__anext__()
        else:
            return self.__next__()

    def __iter__(self):
        self.generator = None
        self.generator_is_async = None
        return self

    def __next__(self):
        if self.generator is None:
            self.generator = self.result_sync()
            self.generator_is_async = inspect.isasyncgen(self.generator)

        try:
            return next(self.generator)
        except StopIteration:
            raise StopAsyncIteration

    def set_contexts(self, *contexts: t.Any | list[t.Any], clear: bool = False):
        if clear:
            self.contexts.clear()
        for value in contexts:
            if value is not None and value not in self.contexts:
                self.contexts.append(value)

    def result_sync(self) -> t.Any:
        chains = self.__get_call_chain__()
        chain_data = []
        last_value = None
        last_context = None
        for chain in chains:
            if isinstance(chain, GetAttrChain):
                if callable(chain.item):
                    last_value = chain.item
                elif hasattr(last_value, chain.item):
                    last_value = getattr(last_value, chain.item)
                else:
                    last_value, last_context = self.__getattr_from_contexts__(chain.item)
            elif isinstance(chain, CallChain):
                call_args, call_kwargs = self.__get_call_args__(chain, chain_data, last_value)
                last_value = last_value(*call_args, **call_kwargs)
                chain_data.append((chain, last_value, last_context))
            else:
                last_value = chain.data
                chain_data.append((chain, last_value, last_context))

        return last_value

    async def __result_async__(self) -> t.Any:
        chains = self.__get_call_chain__()
        chain_data = []
        last_value = None
        last_context = None
        for chain in chains:
            if isinstance(chain, GetAttrChain):
                if callable(chain.item):
                    last_value = chain.item
                elif hasattr(last_value, chain.item):
                    last_value = getattr(last_value, chain.item)
                else:
                    last_value, last_context = self.__getattr_from_contexts__(chain.item)
            elif isinstance(chain, CallChain):
                call_args, call_kwargs = self.__get_call_args__(chain, chain_data, last_value)
                if inspect.isawaitable(last_value):
                    last_value = last_value(*call_args, **call_kwargs)
                else:
                    args = partial(last_value, *call_args, **call_kwargs)
                    last_value = await asyncio.get_running_loop().run_in_executor(None, args)
            else:
                last_value = chain.data

            if inspect.isawaitable(last_value):
                last_value = await last_value

            if chain.__class__ == Chain or isinstance(chain, CallChain):
                chain_data.append((chain, last_value, last_context))
        return last_value

    def __get_call_chain__(self) -> list[Chain | GetAttrChain | CallChain]:
        chains = []
        chained = self
        while chained:
            chains.append(chained)
            chained = chained.parent
        chains.reverse()
        return chains

    def __get_call_args__(self, chain, chain_data, last_value):
        last_context = chain_data[-1][2]
        if chain.parent.pipe:
            pipe_data = chain_data[-1][1]
            args = (pipe_data,) + chain.args
        else:
            args = chain.args

        try:
            params = inspect.signature(last_value).parameters
            needs_self = params.get('self', None) is not None
            needs_cls = params.get('cls', None) is not None
            if needs_self or needs_cls:
                args = (last_context,) + args
        except ValueError:
            pass
        return (args, chain.kwargs)

    def __getattr_from_contexts__(self, name: str) -> t.Any | None:
        for context in self.contexts + [builtins]:
            if name in dir(context):
                return getattr(context, name), context
            elif isinstance(context, Iterable) and name in context:
                return context[name], context

        raise AttributeError("{0} cannot find attribute '{1}'".format(self, name))


class GetAttrChain(Chain):
    __slots__ = ('item',)

    def __init__(self,
                 parent: Chain,
                 item: str | t.Callable,
                 context: t.Optional[t.Any | list[t.Any]] = [],
                 pipe: t.Optional[bool] = False):
        super().__init__(parent=parent, context=context, pipe=pipe)
        self.item = item


class CallChain(Chain):
    __slots__ = ('args', 'kwargs')

    def __init__(self,
                 parent: Chain,
                 args=None,
                 kwargs=None,
                 context: t.Optional[t.Any | list[t.Any]] = [],
                 pipe: t.Optional[bool] = False):
        super().__init__(parent=parent, context=context, pipe=pipe)
        self.args = args or ()
        self.kwargs = kwargs or {}
