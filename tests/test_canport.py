from labgrid.resource import CANInterface  # pylint: disable=import-error


class TestSocketCANInterface:
    def test_instanziation(self):
        s = CANInterface(None, 'can', ifname='can0')
        assert (s.ifname == 'can0')

    def test_instanziation_with(self, target):
        s = CANInterface(target, 'can', ifname='can0', bitrate=250000)
        assert (s.ifname == 'can0')
        assert (s.bitrate == 250000)
        assert s in target.resources
