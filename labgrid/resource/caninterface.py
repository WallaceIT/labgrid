import attr

from ..factory import target_factory
from .common import Resource


@target_factory.reg_resource
@attr.s(eq=False)
class CANInterface(Resource):
    """The basic CANInterface contains an interface name and CAN parameters

    Args:
        type (str): type of the CAN interface, defaults to 'socketcan'
        ifname (str): name of the CAN interface
        bitrate (int): CAN bitrate (1-1000000), defaults to 250000
        samplepoint (float): CAN sample point (0.001-1.000), defaults to 0.750
        fd (bool): enable CAN-FD, defaults to False
        databitrate (int): CAN-FD data bitrate (1-25000000), defaults to 10000000
    """
    type = attr.ib(default='socketcan', validator=attr.validators.instance_of(str))
    ifname = attr.ib(default=None, validator=attr.validators.instance_of(str))
    bitrate = attr.ib(default=250000, validator=attr.validators.instance_of(int))
    samplepoint = attr.ib(default=0.750, validator=attr.validators.instance_of(float))
    fd = attr.ib(default=False, validator=attr.validators.instance_of(bool))
    databitrate = attr.ib(default=1000000, validator=attr.validators.instance_of(int))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        if self.ifname is None:
            raise ValueError("CANInterface must be configured with a ifname")
