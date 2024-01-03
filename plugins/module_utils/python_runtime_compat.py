# -*- coding: utf-8 -*-

# Copyright Sviatoslav Sydorenko
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Collection of cross-Python compatibility shims."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import signal

try:
    import typing as t  # noqa: F401
except ImportError:
    pass


from ansible.module_utils.six import raise_from
from ansible.module_utils.six.moves import shlex_quote as _shlex_quote


try:
    from shlex import join as shlex_join  # Python 3.8+
except ImportError:
    # Vendored from
    # https://github.com/python/cpython/blob/e500cc0/Lib/shlex.py#L316-L318
    def shlex_join(  # noqa: WPS440
            split_command,  # noqa: WPS318
    ):  # type: (t.Iterable[str]) -> str
        """Return a shell-escaped string from *split_command*."""
        return ' '.join(_shlex_quote(arg) for arg in split_command)


try:
    globals()['TimeoutError'] = TimeoutError  # noqa: WPS421  # Python 3
except NameError:
    from errno import ETIMEDOUT as _ETIMEDOUT

    class TimeoutError(OSError):  # noqa: WPS125
        """An exception shim for timeout errors under Python 2."""

        def __init__(  # noqa: WPS612
                self,  # noqa: WPS318
                errno=_ETIMEDOUT,  # type: int
                *args,  # type: list
                **kwargs,  # type: dict
        ):  # type: (...) -> None
            """Initialize a timeout error instance."""
            super(TimeoutError, self).__init__(errno, *args, **kwargs)


def get_signal_name(signal_constant):
    try:
        return signal.Signals(signal).name  # Python 3
    except AttributeError:
        pass

    # Python 2:
    try:
        return next(
            signal_name
            for signal_name in dir(signal)  # noqa: WPS421
            if signal_name.startswith('SIG') and signal_name[3] != '_'
            and getattr(signal, signal_name) == signal_constant
        )
    except StopIteration as iter_stop_exc:
        raise raise_from(LookupError, iter_stop_exc)  # MyPy hack


__all__ = ('get_signal_name', 'shlex_join', 'TimeoutError')  # noqa: WPS410
