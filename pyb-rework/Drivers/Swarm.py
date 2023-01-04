"""Driver that (in theory) sends messages over the SWARM module
very untested and written entirely using datasheet info
"""

import AsyncUART
import board

SWARM_UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.TX, board.RX) #TODO: actual uart definition

ready_to_receive: bool = False
ready_to_send: bool = False

async def wait_for_bootloader_finish():
    """If the module has not already finished its bootup sequence this will wait asynchronously
    until it does
    """
    while not ready_to_receive:
        await SWARM_UART.async_read_until_forever(b'$M138 BOOT,RUNNING*49')
        ready_to_receive = True

async def wait_for_init():
    """If the module is not ready to send data, this will wait asynchronously
    until it is
    """
    while not ready_to_send:
        await wait_for_bootloader_finish()
        await SWARM_UART.async_read_until_forever(b'$M138 DATETIME*35')
        ready_to_send = True

def send_message_no_wait(message: str):
    """Sends a message and immediately returns regardless of if the message was actually
    sent to a satellite

    :param message: Message to send
    :type message: str
    """
    serialized_msg_no_checksum = "$TD " + message

    checksum_bytes = serialized_msg_no_checksum.encode('ascii')
    checksum = 0
    for b in checksum_bytes:
        checksum ^= b
    checksum_str = format(checksum, "02x")

    serialized_msg = serialized_msg_no_checksum + "*" + checksum_str
    SWARM_UART.write(serialized_msg)

async def receive_msg():
    """Waits until a valid message is received

    :return: Received message
    :rtype: str
    """
    return await SWARM_UART.async_readline_forever()

async def send_message(message: str):
    """Sends a message and waits until the module confirms that it was sent to the satellites

    :param message: Message to send
    :type message: str
    :raises Exception: Message failed to send for some reason
    """
    send_message_no_wait(message)
    response = receive_msg()
    response_relevant = response[0:6]
    if response_relevant != b'$TD OK': #TODO: better check
        raise Exception("COMMS_ERROR, MSG=" + bytes.decode(response, 'ascii'))