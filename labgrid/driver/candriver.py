import attr
import can
import subprocess
import time

from .common import Driver
from ..factory import target_factory
from ..util.proxy import proxymanager
from ..resource.caninterface import CANInterface
from ..resource.remote import NetworkCANInterface
from ..step import step
from ..util.helper import processwrapper
from ..util.timeout import Timeout


@target_factory.reg_driver
@attr.s(eq=False)
class CANDriver(Driver):
    bindings = {
        "interface": {"CANInterface", "NetworkCANInterface"},
    }

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    def on_activate(self):
        self.configure_interface()
        self.set_interface_up()
        if isinstance(self.interface, CANInterface):
            self._bus = can.Bus(interface=self.interface.type, channel=self.interface.ifname,
                                bitrate=self.interface.bitrate, fd=self.interface.fd,
                                data_bitrate=self.interface.databitrate)
        else:
            host, port = proxymanager.get_host_and_port(self.interface)
            self._bus = can.Bus(interface='socketcand', host=host, port=port,
                                channel=self.interface.ifname)
    def on_deactivate(self):
       self._bus.shutdown()
       self.set_interface_down()

    def _wrap_command(self, args):
        wrapper = ["sudo", "labgrid-can-setup"]

        if self.interface.command_prefix:
            # add ssh prefix, convert command passed via ssh (including wrapper) to single argument
            return self.interface.command_prefix + [" ".join(wrapper + args)]
        else:
            # keep wrapper and args as-is
            return wrapper + args

    @step(args=["state"])
    def _set_interface(self, state):
        """Set interface to given state."""
        if self.interface.type == 'socketcan' or isinstance(self.interface, NetworkCANInterface):
            cmd = self._wrap_command([self.interface.ifname, state])
            subprocess.check_call(cmd)

    @Driver.check_bound
    def set_interface_up(self):
        """Set bound interface up."""
        self._set_interface("up")

    @Driver.check_active
    def set_interface_down(self):
        """Set bound interface down."""
        self._set_interface("down")

    def _is_socketcan(self):
        return self.interface.type == 'socketcan' or isinstance(self.interface, NetworkCANInterface)

    def _get_state(self):
        """Returns the bound interface's operstate."""
        if_state = self.interface.extra.get("state")
        if if_state:
            return if_state

        if self._is_socketcan():
            cmd = self.interface.command_prefix + ["cat", f"/sys/class/net/{self.interface.ifname}/operstate"]
            output = processwrapper.check_output(cmd).decode("ascii")
            if_state = output.strip()
            return if_state

        # If state cannot be detected, assume it's up
        return "up"

    @Driver.check_active
    def get_state(self):
        """Returns the bound interface's operstate."""
        return self._get_state()

    @step(title="wait_state", args=["expected_state", "timeout"])
    def _wait_state(self, expected_state, timeout=60):
        """Wait until the expected state is reached or the timeout expires."""
        timeout = Timeout(float(timeout))

        while True:
            if self._get_state() == expected_state:
                return
            if timeout.expired:
                raise TimeoutError(
                    f"exported interface {self.interface.ifname} did not go {expected_state} within {timeout.timeout} seconds"
                )
            time.sleep(0.1)

    @Driver.check_active
    def wait_state(self, expected_state, timeout=60):
        """Wait until the expected state is reached or the timeout expires."""
        self._wait_state(expected_state, timeout=timeout)

    @Driver.check_bound
    def configure_interface(self):
        """Configure interface."""
        if self._is_socketcan():
            cmd = self._wrap_command([self.interface.ifname, "conf",
                                      "--bitrate", str(self.interface.bitrate),
                                      "--sample-point", str(self.interface.samplepoint),
                                      ])
            subprocess.check_call(cmd)

    def get_export_vars(self):
        export_vars = {
            "ifname": self.interface.ifname,
            "bitrate": str(self.interface.bitrate),
            "samplepoint": str(self.interface.samplepoint),
            "fd": str(self.interface.fd),
            "databitrate": str(self.interface.databitrate),
        }
        if isinstance(self.interface, CANInterface):
            export_vars["type"] = self.interface.type
        else:
            host, port = proxymanager.get_host_and_port(self.interface)
            export_vars["host"] = host
            export_vars["port"] = str(port)
        return export_vars

    @Driver.check_active
    def get_bus(self):
        """Return the raw python-can bus instance."""
        return self._bus

    @Driver.check_active
    def send(self, arbitration_id, data, is_extended_id=False):
        """Send a single CAN message."""
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=is_extended_id)
        self._bus.send(msg, timeout=0)

    @Driver.check_active
    def recv(self):
        """Receive a single CAN message."""
        msg = self._bus.recv(timeout=0)
        if msg is not None and not msg.is_error_frame:
            return (msg.arbitration_id, msg.data)
        return (None, None)

