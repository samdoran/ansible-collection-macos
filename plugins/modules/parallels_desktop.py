#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright Sviatoslav Sydorenko
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Support for making sure that Parallels Desktop stays dead."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {  # noqa: WPS407
    'metadata_version': '1.1',
    'status': [
        'preview',
    ],
    'supported_by': 'community',
}


DOCUMENTATION = """
---

module: parallels_desktop
version_added: 2.5.0

author:
- Sviatoslav Sydorenko (@webknjaz)

short_description: Make sure that Parallels Desktop is not running
description:
- Ask Parallels Desktop to terminate in many ways.
- This module attempts to kill Parallels using a C(osascript) command,
- waiting for it to terminate and then following up with
- C(kill -SIGTERM) and finally with C(kill -SIGKILL) as the last
- resort. The use of the fallbacks depends on the ``state`` requested.
notes: []

options:
  state:
    default: started
    description: >-
      The most ruthless method allowed for stopping
      the Parallels Desktop application execution,
      unless set to ``started``.
    choices:
    - started
    - terminated
    - killed
    - murdered
    type: str

...
"""

EXAMPLES = """
---

- name: Make sure that Parallels Desktop is turned off
  samdoran.macos.parallels_desktop:
    state: murdered

...
"""

RETURN = """
---

cmd:
  description: Raw underlying command
  returned: failure
  type: list

cmd_string:
  description: Underlying command as a string
  returned: failure
  type: str

msg:
  description: Execution details
  returned: always
  type: str

rc:
  description: Return code of the underlying command
  returned: failure
  type: int

stdout:
  description: Standard output of the underlying command
  returned: failure
  type: str

stderr:
  description: Error output of the underlying command
  returned: failure
  type: str

...
"""

import errno
import os
import signal
import time
import traceback
from functools import partial

try:
    import typing as t  # noqa: F401
except ImportError:
    pass


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import PY2, raise_from

from ..module_utils.python_runtime_compat import (  # noqa: WPS300
    get_signal_name,
    shlex_join as _shlex_join,
    TimeoutError,
)


VM_SHUTDOWN_GRACE_DELAY = 30


PARALLELS_DESKTOP_APP_NAME = 'Parallels Desktop'
PARALLELS_DESKTOP_CLI_NAME = 'prlctl'
PARALLELS_DESKTOP_CLI_LOCATION = '/usr/local/bin/'
PARALLELS_DESKTOP_PROCESS_NAME = 'prl_client_app'


ANTICIPATED_KILL_FAILURES = (
    OSError if PY2
    else (ProcessLookupError, PermissionError)
)  # type: Exception | tuple[Exception, ...]


class ParallelsDesktopModuleError(RuntimeError):
    """Exception representing an Ansible module generic failure."""

    def __init__(
            self,  # noqa: WPS318
            msg,  # type: str
            error_args,  # type: dict
            *args,  # type: list
            **kwargs  # type: dict
    ):  # type: (...) -> None
        """Initialize a Parallels Desktop error instance.

        :param msg: Error message, overrides ``error_args['msg']`` if not set.

        :param error_args: A mapping with arbitrary context.
        """
        super(ParallelsDesktopModuleError, self).__init__(msg, *args, **kwargs)

        self.error_args = error_args
        self.error_args['msg'] = self.error_args.get('msg', msg)

    def __str__(self):  # type: () -> str
        return self.error_args['msg']

    def __unicode__(self):  # type: () -> str
        return to_text(str(self))

    def __repr__(self):  # type: () -> str
        return (
            '<{cls}(msg={msg!s}, error_args={error_args!s})> '
            'at 0x{object_address_str:x}'.format(
                cls=self.__class__.__name__,
                error_args=repr(self.error_args),
                msg=repr(str(self)),
                object_address_str=id(self),
            )
        )


class CmdFailedError(ParallelsDesktopModuleError):
    """Exception representing an arbitraty command failure."""

    def __init__(
            self,  # noqa: WPS318
            msg,  # type: str
            error_args,  # type: dict
            *args,  # type: list
            **kwargs  # type: dict
    ):  # type: (...) -> None
        """Initialize a failed command error instance.

        :param msg: Error message, overrides ``error_args['msg']`` if not set.

        :param error_args: A mapping with arbitraty context, must contain
                           ``cmd`` and ``rc`` -- failed command and return
                           code respectively.
        """
        for mandatory_key in 'cmd', 'rc':
            if mandatory_key not in error_args:
                raise AssertionError(
                    '`error_args` argument must contain `{missing_arg!s}` key'.
                    format(missing_arg=mandatory_key),
                )

        kwargs['error_args'] = error_args
        super(CmdFailedError, self).__init__(msg, *args, **kwargs)

    def __str__(self):  # type: () -> str
        """Render the exception instance as a string."""
        msg = super(CmdFailedError, self).__str__()
        return '[rc={rc}] {msg}'.format(msg=msg, rc=self.error_args['rc'])

    def __repr__(self):  # type: () -> str
        """Render the exception instance representation as a string."""
        parent_repr = super(CmdFailedError, self).__repr__()
        return '{parent_repr} [failed with rc={rc}]'.format(
            parent_repr=parent_repr,
            rc=self.error_args['rc'],
        )


def process_syscall_errors(
        kill_process,  # type: t.Callable[[int, signal.Signals], None]  # noqa: WPS318
):  # type: (...) -> t.Callable[[int, signal.Signals], None]
    """Decorate process-killer function suppressing expected errors.

    The replacement function fully suppresses "No such process" and turns
    "Operation not permitted" :exc:`CmdFailedError`, letting anything else
    bubble up the call stack.

    :raises CmdFailedError: On "Operation not permitted".
    """

    def kill_process_wrapper(  # noqa: WPS430
            pid,  # type: int  # noqa: WPS318
            process_signal,  # type: signal.Signals
    ):  # type: (...) -> None
        try:
            kill_process(pid, process_signal)
        except ANTICIPATED_KILL_FAILURES as proc_exc:
            # NOTE: `ProcessLookupError` (Python 3) or
            # NOTE: `OSError: [Errno 3] No such process` (Python 2) is success.
            #
            # NOTE: `PermissionError` (Python 3) or
            # NOTE: `OSError: [Errno 1] Operation not permitted` (Python 2) is
            # NOTE: to be reraised.
            if proc_exc.errno == errno.ESRCH:
                return

            # NOTE: Fail on errno.EPERM -> PermissionError and others
            # >>> get_signal_name(process_signal)
            # 'SIGKILL'
            signal_name = get_signal_name(process_signal)
            cmd = 'kill', '-{signal!s}'.format(signal=signal_name), pid
            res = {
                'cmd': cmd,
                'rc': proc_exc.errno,
                'stdout': '',
                'stderr': proc_exc.strerror,
            }

            raise_from(
                CmdFailedError(
                    'Running `{cmd}` was unsuccessful'.
                    format(cmd=_shlex_join(cmd)),
                    error_args=res,
                ),
                proc_exc,
            )
            raise CmdFailedError  # NOTE: MyPy hack

    return kill_process_wrapper


class ParallelsDesktopAnsibleModule(AnsibleModule):  # noqa: WPS214
    """Ansible module.

    Implements a class method entrypoint and the main module logic.
    """

    params = {}  # type: dict[str, str]

    def __init__(self):  # type: () -> None
        """Initialize module prerequisites.

        This sets up the expected argument specification and the mandatory
        executables that are expected to be present on the target system.
        """
        super(ParallelsDesktopAnsibleModule, self).__init__(
            argument_spec={
                'state': {
                    'default': 'started',
                    'choices': [
                        'started',
                        'terminated',
                        'killed',
                        'murdered',
                    ],
                },
            },
            supports_check_mode=True,
        )

        self.osascript = self.get_bin_path(
            'osascript',
            required=True,
        )  # type: str
        self.pgrep_bin = self.get_bin_path('pgrep', required=True)  # type: str
        self.prlctl_exe = self.get_bin_path(
            PARALLELS_DESKTOP_CLI_NAME,
            opt_dirs=[PARALLELS_DESKTOP_CLI_LOCATION],
            required=True,
        )  # type: str

    @classmethod
    def execute(cls):  # type: () -> None
        """Start invocation processing on initialized Ansible module."""
        cls().run()

    @property
    def requested_state(self):  # type: () -> str
        """Return the requested state."""
        return self.params['state']

    def run(self):  # type: () -> None
        """Execute action chosen."""
        try:
            action_result = (
                self.ensure_app_started() if self.requested_state == 'started'
                else self.ensure_app_terminated()
            )
        except ParallelsDesktopModuleError as mod_err:
            self.fail_json(**mod_err.error_args)
        except BaseException:  # noqa: WPS424
            self.fail_json(
                exception=traceback.format_exc(),
                msg='An unexpected error happened.',
            )
        else:
            msg_parts = [
                'Achieving the `{state!s}` state succeeded.'.format(
                    state=self.requested_state,
                ),
            ]
            if 'msg' in action_result:
                msg_parts.append(action_result['msg'])  # noqa: WPS529

            action_result['msg'] = ' '.join(msg_parts)

            self.exit_json(**action_result)

    def run_with_raise(
            self,  # noqa: WPS318
            cmd,  # type: str | list[str] | tuple[str]
    ):  # type: (...) -> dict[str, list | str | int]
        """Invoke given command checking for failure.

        :raises CmdFailedError: On unsuccessful return code.
        """
        if not isinstance(cmd, str):
            cmd = list(cmd)
        return_code, standard_output, error_output = self.run_command(
            cmd,
            encoding='utf-8',
            environ_update={},
        )
        cmd_string = cmd if isinstance(cmd, str) else _shlex_join(cmd)
        res = {
            'cmd': cmd,
            'cmd_string': cmd_string,
            'rc': return_code,
            'stdout': standard_output,
            'stderr': error_output,
        }

        if return_code != 0:
            self.debug(
                'Running `{cmd!s}` failed with the return '  # noqa: G001
                'code of `{rc:d}`'.
                format(cmd=cmd_string, rc=return_code),
            )
            raise CmdFailedError(
                'Running `{cmd!s}` was unsuccessful'.
                format(cmd=cmd_string),
                error_args=res,
            )

        self.debug(
            'Running `{cmd!s}` succeeded'.  # noqa: G001
            format(cmd=cmd_string),
        )

        return res

    def get_parallels_pid(self):  # type: () -> int
        """Look up PID of the running Parallels instance.

        :raises LookupError: If there's no Parallels process.
        """
        pgrep_cmd_exec_args = (
            self.pgrep_bin,
            '-x',
            PARALLELS_DESKTOP_PROCESS_NAME,
        )  # type: tuple[str, ...]

        try:
            command_result = self.run_with_raise(pgrep_cmd_exec_args)
        except CmdFailedError as cmd_err:
            raise_from(
                LookupError(
                    'No process named `{proc_name!s}` found running. '
                    '{cmd_err!s}'.
                    format(
                        proc_name=PARALLELS_DESKTOP_PROCESS_NAME,
                        cmd_err=cmd_err,
                    ),
                ),
                cmd_err,
            )
            raise LookupError  # NOTE: MyPy hack

        return int(command_result['stdout'].strip())

    def get_running_vm_ids(self):  # type: () -> list[str]
        """Return a list of running VM UUIDs."""
        vm_list_output = self.run_with_raise((self.prlctl_exe, 'list'))
        return [
            output_line.split()[0].strip()
            for output_line in vm_list_output['stdout'].splitlines()[1:]
        ]

    def ensure_running_vms_stopped(self):  # noqa: WPS213  # type: () -> None
        """Stop the VMs if there's any running.

        This is implemented in several stages:
        * First, the ACPI signal is sent to the VMs
        * Then, a 30-second delay gives those VMs to shut down gracefully
        * Finally, the remaining VMs are force-killed
        """
        vm_ids = self.get_running_vm_ids()

        if not vm_ids:
            self.debug('No VMs are online. Nothing to do.')
            return

        if self.check_mode:
            return

        for virtual_machine_uuid in vm_ids:
            self.run_with_raise(
                (self.prlctl_exe, 'stop', virtual_machine_uuid, '--acpi'),
            )

        self.log('Taking a 30s nap to allow the VMs shut down gracefully...')
        time.sleep(VM_SHUTDOWN_GRACE_DELAY)

        remaining_vm_ids = self.get_running_vm_ids()

        if not remaining_vm_ids:
            self.debug('Gracefull shutdown exited all the VMs successfully...')
            return

        self.debug(
            'Gracefull shutdown failed to exit {amount!s} '  # noqa: G001
            'the VMs...'.
            format(
                amount='some of' if len(remaining_vm_ids) < len(vm_ids)
                else 'all',
            ),
        )

        if not (set(vm_ids) >= set(remaining_vm_ids)):  # noqa: WPS508
            self.warn('A new VM got spawned while shutting down all VMs.')

        for virtual_machine_uuid in remaining_vm_ids:  # noqa: WPS440
            self.run_with_raise(
                (self.prlctl_exe, 'stop', virtual_machine_uuid, '--kill'),
            )

        remaining_vm_ids = self.get_running_vm_ids()

        if remaining_vm_ids:
            self.warn(
                'New VMs got spawned while force-killing down '  # noqa: G001
                'all VMs: {vms!s}.'.format(vms=', '.join(remaining_vm_ids)),
            )

    def wait_for_parallels_app_to_die(
            self,  # noqa: WPS318
            original_pid,  # type: int
            wait_cycles=100,  # type: int
    ):  # type: (...) -> None
        """Block until Parallels Desktop is dead or timeout reached.

        :param original_pid: Process ID for running the check against.
        :param wait_cycles: Number of half-a-second loop iterations to wait for
                            Parallels to shut down.

        :raises TimeoutError: When the wait cycle exceeded.
        :raises ParallelsDesktopModuleError: If Parallels Desktop process is
                                             substituted suddenly.
        """
        # NOTE: This emulates `Contents/Resources/postflight`'s waiting
        # NOTE: behavior except for the higher check frequency for better
        # NOTE: responsiveness.
        # FIXME: Should this implement a jittered exponential backoff instead??
        try:
            self.get_parallels_pid()
        except LookupError:
            return

        cycle_delay = 0.5
        for wait_cycle in range(wait_cycles):
            time.sleep(cycle_delay)
            self.debug(
                'Waitied for {duration!s}...'.  # noqa: G001
                format(duration=cycle_delay * wait_cycle),
            )

            try:
                parallels_desktop_pid = self.get_parallels_pid()
            except LookupError:
                break
            if parallels_desktop_pid != original_pid:
                raise ParallelsDesktopModuleError(
                    msg='Another `{app_name}` instance got re-spawned '
                    'unexpectedly by an external process. Make sure not '
                    'to start {app_name} while this module is running...'.
                    format(app_name=PARALLELS_DESKTOP_APP_NAME),
                    error_args={
                        'Original {app_name} PID'.
                        format(app_name=PARALLELS_DESKTOP_APP_NAME):
                        original_pid,
                        'New {app_name} PID'.
                        format(app_name=PARALLELS_DESKTOP_APP_NAME):
                        parallels_desktop_pid,
                    },
                )
        else:
            # Still running
            raise TimeoutError(
                'Timed out waiting for process PID {pid:d}.'.
                format(pid=original_pid),
            )

    def kindly_ask_parallels_desktop_app_to_quit(self):  # type: () -> None
        """Tell Parallels to quit via ``osascript``.

        This function suppresses the following known situations:
        * Parallels Desktop is showing the Update Available window during start
        * The command is invoked under a user that is unable to look into the
          apps being run under different users.
        """
        osascript_cmd_exec_args = (
            self.osascript,
            '-e',
            'tell application "{app_name}" to quit'.
            format(app_name=PARALLELS_DESKTOP_APP_NAME),
        )
        try:
            self.run_with_raise(osascript_cmd_exec_args)
        except CmdFailedError as cmd_err:
            process_error_code = 1

            user_cancelled_error_msg = (  # Stuck on Update Available on start
                '40:44: execution error: Parallels Desktop got an error: '
                'User canceled. (-128)'
            )
            app_isnt_running_error_msg = (  # Running under different user
                '40:44: execution error: Parallels Desktop got an error: '
                'Application isn’t running. (-600)'
            )

            expected_error_messages = {
                app_isnt_running_error_msg,
                user_cancelled_error_msg,
            }

            is_generic_error = cmd_err.error_args['rc'] == process_error_code
            is_error_message_expected = (
                cmd_err.error_args['stderr'] in expected_error_messages
            )
            if is_generic_error and is_error_message_expected:
                pass

            raise

    def ensure_app_started(  # noqa: WPS231
            self,  # noqa: WPS318
    ):  # type: () -> dict[str, bool | str]
        """Make sure the Parallels Desktop app is running."""
        try:
            parallels_pid = self.get_parallels_pid()
        except LookupError:
            parallels_pid = -1
            spawn_parallels_cmd = 'open', '-a', 'Parallels Desktop', '--hide'
            # NOTE: This may error out with rc=1 and the following stderr:
            # NOTE: "LSOpenURLsWithRole() failed for the application
            # NOTE: /Applications/Parallels Desktop.app with error -610.\n"

            if not self.check_mode:
                self.run_with_raise(spawn_parallels_cmd)
                parallels_pid = self.get_parallels_pid()

            return {
                'msg': 'The {app!s} app (process: `{proc!s}`; '
                'PID: `{pid:d}`) has been started successfully.'.
                format(
                    app=PARALLELS_DESKTOP_APP_NAME,
                    pid=parallels_pid,
                    proc=PARALLELS_DESKTOP_PROCESS_NAME,
                ),
                'changed': True,
            }

        return {
            'msg': 'The {app!s} app (process: `{proc!s}`; '
            'PID: `{pid:d}`) is already running.'.
            format(
                app=PARALLELS_DESKTOP_APP_NAME,
                pid=parallels_pid,
                proc=PARALLELS_DESKTOP_PROCESS_NAME,
            ),
            'changed': False,
        }

    def ensure_app_terminated(  # noqa: WPS231
            self,  # noqa: WPS318
    ):  # type: () -> dict[str, bool | str]
        """Make sure the Parallels Desktop app isn't running.

        If it does, attempt terminating in 3 fallback stages:
        * Using ``osascript`` (stops here, if the `terminated` state
          is requested)
        * Using ``SIGTERM`` kill signal (stops if the requested state
          is `killed`)
        * Using ``SIGKILL`` kill signal (stops if the requested state
          is `murdered`)

        This function attempts to shut down any running VMs before attempting
        to do the same to the Parallels Desktop app itself.

        :raises ParallelsDesktopModuleError: If the procedure hasn't succeeded.
        """
        try:
            parallels_pid = self.get_parallels_pid()
        except LookupError as lookup_error:
            return {
                'msg': str(lookup_error),
                'changed': False,
            }

        terminate_parallels = process_syscall_errors(
            partial(os.kill, parallels_pid, signal.SIGTERM),
        )
        destroy_parallels = process_syscall_errors(
            partial(os.kill, parallels_pid, signal.SIGKILL),
        )
        parallels_termination_stages = (
            (
                'terminated',
                self.kindly_ask_parallels_desktop_app_to_quit,
                100,
            ),
            ('killed', terminate_parallels, 100),
            ('murdered', destroy_parallels, 5),
        )

        self.ensure_running_vms_stopped()

        killing_error_message = None
        for stage, kill_parallels, wait_cycles in parallels_termination_stages:
            if not self.check_mode:
                kill_parallels()

            try:
                if not self.check_mode:
                    self.wait_for_parallels_app_to_die(
                        parallels_pid, wait_cycles,
                    )
            except TimeoutError as timeout_exc:
                killing_error_message = str(timeout_exc)
            else:
                return {
                    'msg': 'The {app!s} app (process: `{proc!s}`; '
                    'PID: `{pid:d}`) has been {stage!s}.'.
                    format(
                        app=PARALLELS_DESKTOP_APP_NAME,
                        pid=parallels_pid,
                        proc=PARALLELS_DESKTOP_PROCESS_NAME,
                        stage=stage,
                    ),
                    'changed': True,
                }

            if self.requested_state == stage:
                break

        raise ParallelsDesktopModuleError(
            changed=False,
            msg='Failed to terminate the {app!s} app '
            '(process: `{proc!s}`): {msg!s}'.
            format(
                app=PARALLELS_DESKTOP_APP_NAME,
                msg=killing_error_message,
                proc=PARALLELS_DESKTOP_PROCESS_NAME,
            ),
        )


if __name__ == '__main__':
    ParallelsDesktopAnsibleModule.execute()
