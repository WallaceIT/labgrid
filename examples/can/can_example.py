import time

def test_simple_send(can):
    """
    Test the sending of a single message.
    """
    arbitration_id = 0xC0FFEE
    data = [0, 25, 0, 1, 3, 1, 4, 1]

    can.send(arbitration_id, data, is_extended_id=True)

    # Let anyone receive the message
    time.sleep(1)

def test_simple_recv(can):
    """
    Test the reception of a single message.

    One or more messages are supposed to be in the CAN ingress buffer.
    """

    # Wait for a messagge
    time.sleep(1)

    arbitration_id, _ = can.recv()
    assert arbitration_id is not None, "No message received"

def test_uds_comm(can):
    """
    Test UDS communication.

    Test a complex scenario with UDS communication, using can-isotp and
    python-udsoncan.
    """

    import isotp
    from udsoncan.connections import PythonIsoTpConnection
    import udsoncan.client
    import udsoncan.configs

    bus = can.get_bus()

    # Define ISTOPT transport parameters. Refer to isotp documentation for full details.
    isotp_params = {
        'stmin': 32,
        'blocksize': 8,
        'wftmax': 0,
        'tx_data_length': 8,
        'tx_data_min_length': None,
        'tx_padding': 0xFF,
        'rx_flowcontrol_timeout': 1000,
        'rx_consecutive_frame_timeout': 1000,
        'override_receiver_stmin': None,
        'max_frame_size': 4095,
        'can_fd': False,
        'bitrate_switch': False,
        'rate_limit_enable': False,
        'rate_limit_max_bitrate': 1000000,
        'rate_limit_window_size': 0.2,
        'listen_mode': False,
    }

    # Define ISOTP address for UDS communication
    isotp_addr = isotp.Address(isotp.AddressingMode.Normal_29bits, rxid=0x18DA0201, txid=0x18DA0102)

    # Prepare UDS configuration
    config = dict(udsoncan.configs.default_client_config)
    config['data_identifiers'] = {
        'default' : '>H',
        0xF190 : udsoncan.AsciiCodec(17)
    }

    # Instantiate ISOTP stack
    stack = isotp.CanStack(bus, address=isotp_addr, params=isotp_params)

    # Connect UDS to ISOTP stack
    conn = PythonIsoTpConnection(stack)
    with udsoncan.client.Client(conn,  request_timeout=2, config=config) as client:
        vin = client.read_data_by_identifier_first(0xF190)
        assert vin == '0123456789ABCDEF_'
