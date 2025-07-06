import pytest


@pytest.fixture()
def can(target):
    return target.get_driver("CANDriver")
