import pytest

from labgrid.driver import CANDriver
from labgrid.exceptions import NoSupplierFoundError


class TestCANDriver:
    def test_instanziation_fail_missing_port(self, target):
        with pytest.raises(NoSupplierFoundError):
            CANDriver(target, "can")

    def test_instantiation(self, target, can_interface, mocker):
        can_mock = mocker.patch('can.Bus')
        c = CANDriver(target, "can")
        assert (isinstance(c, CANDriver))
        assert (target.drivers[0] == c)
