"""Unit tests for the Python runtime compat shim."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import errno
import sys

import pytest

from ansible_collections.samdoran.macos.plugins.module_utils.python_runtime_compat import shlex_join
from ansible_collections.samdoran.macos.plugins.module_utils.python_runtime_compat import TimeoutError


pytestmark = pytest.mark.skipif(
    sys.version_info[:2] < (2, 7),
    reason='macOS hosts do not run Python 2.6',
)


@pytest.mark.parametrize(  # noqa: WPS317
    ('segmented_command', 'expected_escaped_command'),
    (
        pytest.param(  # noqa: WPS317
            ('multi word', 'cmd'), "'multi word' cmd",
            id='multi-word arg first',
        ),
        pytest.param(  # noqa: WPS317
            ('one', 'cmd', 'more args'),
            "one cmd 'more args'",
            id='multi-word arg last',
        ),
    ),
)
def test_shlex_join(segmented_command, expected_escaped_command):
    """Verify :py:func:`shlex.join`'s advertised behavior."""
    assert shlex_join(segmented_command) == expected_escaped_command


def test_timeout_error_is_oserror():
    """Test shimmed :exc:`TimeoutError` derives from :exc:`OSError`."""
    assert issubclass(TimeoutError, OSError)


def test_timeout_error_errno():
    """Test :exc:`TimeoutError`'s ``errno`` property's ``ETIMEDOUT``."""
    assert TimeoutError().errno in (errno.ETIMEDOUT, None)  # noqa: WPS510
