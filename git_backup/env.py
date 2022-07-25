import os
from typing import Any, Callable, Dict, Optional, Type, Union

Dtype = Union[Type[bool], Type[str], Type[int], Type[float], Callable[[str, str], Any]]

_handlers: Dict[str, Callable] = {
    "list[str]": lambda v, dtype : [p.strip() for p in v.split(',')]
}

def _coerce(val: str, dtype: Dtype) -> Any:
    # args = []
    prim = True
    if dtype is bool:        
        if isinstance(val, str):
            val = val.lower().strip().replace('0', '').replace('false', '').replace('no', '').strip()
    elif dtype is int:
        if isinstance(val, str):
            val = val.strip().split('.')[0]
    elif dtype is float:
        if isinstance(val, str):
            val = val.strip()
    elif dtype is not str:
        prim = False
        
    return dtype(val) if prim else dtype(val, dtype)

def get_env(key: str, optional = False, default: str = None, dtype: Optional[Union[Dtype, str]] = None):
    val = os.getenv(key, default)
    if dtype:
        if dtype in _handlers:
            dtype = _handlers[dtype]
        if not callable(dtype):
            raise ValueError(f"Invalid dtype. Expected callable or one of: {', '.join(_handlers.keys())}")
        val = _coerce(val, dtype)
    if not optional and val is None:
        raise ValueError(f"Invalid environment. Variable not set: {key}")
    return val