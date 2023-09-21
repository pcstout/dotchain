from __future__ import annotations
import typing as t
from .chain import Chain, GetAttrChain, CallChain


class DotChain:
    __slots__ = ('__chain__')

    def __init__(self, data: t.Any = None,
                 context: t.Optional[t.Any | list[t.Any]] = [],
                 parent: t.Optional[Chain] = None,
                 pipe: t.Optional[bool] = False,
                 **kwargs):
        if 'chain' in kwargs:
            self.__chain__ = kwargs.get('chain')
        else:
            self.__chain__ = Chain(data=data, context=context, parent=parent, pipe=pipe)

    @property
    def Pipe(self) -> t.Self:
        self.__chain__.pipe = True
        return self

    @property
    def Chain(self) -> t.Self:
        self.__chain__.pipe = False
        return self

    def With(self, *contexts: t.Any | list[t.Any], clear: bool = False) -> t.Self:
        self.__chain__.set_contexts(*contexts, clear=clear)
        return self

    def Result(self) -> t.Any:
        return self.__chain__.result_sync()

    def Call(self, callable: t.Callable) -> DotChain:
        attr_chain = GetAttrChain(parent=self.__chain__,
                                  item=callable,
                                  context=self.__chain__.contexts,
                                  pipe=self.__chain__.pipe)
        return DotChain(
            chain=CallChain(parent=attr_chain,
                            context=attr_chain.contexts,
                            pipe=attr_chain.pipe))

    def __getattr__(self, item: str) -> DotChain:
        # https://github.com/python/cpython/issues/69718#issuecomment-1093697247
        if item.startswith('__'):
            raise AttributeError(item)
        return DotChain(
            chain=GetAttrChain(self.__chain__,
                               item,
                               context=self.__chain__.contexts,
                               pipe=self.__chain__.pipe))

    def __call__(self, *args, **kwargs) -> DotChain:
        return DotChain(
            chain=CallChain(self.__chain__,
                            args=args,
                            kwargs=kwargs,
                            context=self.__chain__.contexts,
                            pipe=self.__chain__.pipe))

    def __await__(self):
        return self.__chain__.__await__()

    def __aiter__(self):
        self.__chain__.__aiter__()
        return self

    def __iter__(self):
        self.__chain__.__iter__()
        return self

    async def __anext__(self):
        return await self.__chain__.__anext__()

    def __next__(self):
        return self.__chain__.__next__()
