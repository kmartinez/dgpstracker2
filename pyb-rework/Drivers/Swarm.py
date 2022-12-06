import AsyncUART
import board

SWARM_UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.TX, board.RX) #TODO: actual uart definition

ready_to_receive: bool = False
ready_to_send: bool = False

async def wait_for_bootloader_finish():
    while not ready_to_receive:
        await SWARM_UART.async_read_until_forever(b'$M138 BOOT,RUNNING*49')
        ready_to_receive = True

async def wait_for_init():
    while not ready_to_send:
        await wait_for_bootloader_finish()
        await SWARM_UART.async_read_until_forever(b'$M138 DATETIME*35')
        ready_to_send = True

def send_message_no_wait(message: str):
    serialized_msg_no_checksum = "$TD " + message

    checksum_bytes = serialized_msg_no_checksum.encode('ascii')
    checksum = 0
    for b in checksum_bytes:
        checksum ^= b
    checksum_str = format(checksum, "02x")

    serialized_msg = serialized_msg_no_checksum + "*" + checksum_str
    SWARM_UART.write(serialized_msg)

async def receive_msg():
    return await SWARM_UART.async_readline_forever()

async def send_message(message: str):
    send_message_no_wait(message)
    response = receive_msg()
    response_relevant = response[0:6]
    if response_relevant != b'$TD OK':
        raise Exception("COMMS_ERROR, MSG=" + bytes.decode(response, 'ascii'))