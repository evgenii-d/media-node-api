"""System Command Executor."""
import logging
from subprocess import run, TimeoutExpired, CalledProcessError
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SysCmdExec:
    """Executes system commands and provides the output."""
    # pylint: disable=too-few-public-methods

    @dataclass
    class Response:
        """The result of a command execution."""
        success: bool
        output: str

    @staticmethod
    def run(args: list[str], timeout: float = None) -> "SysCmdExec.Response":
        """Executes a system command.

        Args:
            args (list[str]): 
                A list of strings representing the command
                and its arguments.
            timeout (float, optional): 
                The maximum time (in seconds) to wait 
                for the command to complete. Defaults to None.

        Returns:
            SysCmdExec.Response: 
                An object containing the result 
                of the command execution.
        """
        args_string = " ".join(args)
        try:
            result = run(args, check=True, timeout=timeout,
                         capture_output=True, text=True)
            logger.info("Command completed: %s", args_string)
            return SysCmdExec.Response(True, result.stdout)
        except TimeoutExpired as error:
            logger.warning("Command timed out: %s\nError: %s",
                           args_string, error)
            return SysCmdExec.Response(False, str(error))
        except CalledProcessError as error:
            logger.warning("Command failed: %s. Return code: %s\nError: %s",
                           args_string, error.returncode, error.stderr)
            return SysCmdExec.Response(False, error.stderr)
        except FileNotFoundError as error:
            logger.warning("Command not found: %s\nError: %s",
                           args_string, error)
            return SysCmdExec.Response(False, str(error))
