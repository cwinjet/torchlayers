import collections
import itertools
import typing

from .. import _inferrable


def is_kwarg(argument: str) -> bool:
    """`True` if argument name is `**kwargs`"""
    return "**" in argument


def is_vararg(argument: str) -> bool:
    """`True` if argument name is `*args`"""
    return "*" in argument and "**" not in argument


def remove_vararg(argument: str) -> str:
    """`True` if argument name is `*args`"""
    return argument.split("*")[1]


def remove_kwarg(argument: str) -> str:
    """Removes `**` in kwargs so those can be assigned in dynamic `__init__` creation"""
    return argument.split("**")[1]


def remove_right_side(argument: str) -> str:
    """Removes default arguments so their names can be used as values or names of variables."""
    return argument.split("=")[0]


def remove_type_hint(argument: str) -> str:
    """Removes any Python type hints.

    Those are incompatible with `exec` during dynamic `__init__` creation
    (at least not without major workarounds).

    Default values (right hand side) is preserved if exists.

    """
    splitted_on_type_hint = argument.split(":")
    no_type_hint = splitted_on_type_hint[0]
    if len(splitted_on_type_hint) > 1:
        splitted_on_default = splitted_on_type_hint[1].split("=")
        if len(splitted_on_default) > 1:
            no_type_hint += "={}".format(splitted_on_default[1])
    return no_type_hint


def get_per_module_index(module: str) -> int:
    """Get integer pointer to `tensor.shape` for the shape inference.

    Almost all modules need `shape[1]` to be inferred.
    Currently only exception being `recurrent` modules, in this case `2` is returned.

    Returns
    -------
    int
        Pointer to `tensor.shape` which should be inferred for specific module.
    """
    if (
        module.__name__
        in _inferrable.torch.recurrent
        + _inferrable.torch.transformer
        + _inferrable.torch.attention
    ):
        return 2
    return 1


def create_vars(
    self,
    non_inferrable_names: typing.Dict[str, Any],
    VARARGS_VARIABLE: str,
    KWARGS_VARIABLE: str,
) -> typing.List[str]:
    """
    Create arguments for

    [TODO:description]

    Parameters
    ----------
    non_inferrable_names : typing.Dict[str, Any]
        [TODO:description]
    VARARGS_VARIABLE : str
        [TODO:description]
    KWARGS_VARIABLE : str
        [TODO:description]

    Returns
    -------
    typing.List[str]:
        [TODO:description]
    """
    dictionary = {**non_inferrable_names, **collections.OrderedDict(vars(self))}

    args = [
        "{}={}".format(key, value)
        for key, value in dictionary.items()
        if not key.startswith("_") and key != "training"
    ]
    varargs = getattr(self, VARARGS_VARIABLE, None)
    if varargs is not None:
        args += [str(var) for var in varargs]

    kwargs = getattr(self, KWARGS_VARIABLE, None)
    if kwargs is not None:
        args += ["{}={}".format(key, value) for key, value in kwargs.items()]

    return args


def process_arguments(arguments):
    processed_arguments = [
        remove_type_hint(remove_right_side(argument)) for argument in arguments
    ]
    return processed_arguments[0], processed_arguments[1:]
