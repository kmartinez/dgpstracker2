import config
from _typeshed import SupportsWrite
from typing_extensions import Literal

def debug(
    *values: object,
    sep: str | None = ...,
    end: str | None = ...,
    file: SupportsWrite[str] | None = ...,
    flush: Literal[False] = ...,
) -> None:
    '''Prints if debugging is on'''
    if config.DEBUG:
        print(*values, sep=sep, end=end, file=file, flush=flush)