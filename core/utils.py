from typing import TypeVar, Generic

T = TypeVar("T")


class Result(Generic[T]):
    def __init__(self, done: bool, content: T):
        self.done = done
        self.result = content
