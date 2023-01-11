"""Module that extends busio's UART with async/await functionality.
"""

import busio
import microcontroller
import asyncio
import binascii
from config import *
import adafruit_logging as logging

logger = logging.getLogger("ASYNC_UART")

class AsyncUART(busio.UART):
    """Extended UART class that includes async versions of some functions.
    Allows asynchronous waiting while data has not been received
    """
    def __init__(
        self,
        tx: microcontroller.Pin,
        rx: microcontroller.Pin,
        *,
        baudrate: int = 9600,
        bits: int = 8,
        parity = None,
        stop: int = 1,
        timeout: int = 1,
        receiver_buffer_size: int = 64,
        ) -> None:
        super().__init__(tx, rx, baudrate=baudrate, bits=bits, parity=parity, timeout=timeout, stop=stop, receiver_buffer_size=receiver_buffer_size)

    async def __async_get_byte_forever(self) -> int:
        """Reads a single byte asynchronously.

        :return: Single byte
        :rtype: int
        """
        while (self.in_waiting < 1): #So this exists apparently whoops
            await asyncio.sleep(0)
        output = super().read(1)[0] #read returns a byte array so we return the first index

        logger.log(5, f"ASYNC_UART_GET_BYTE: {output}")
        return output

    async def async_read_forever(self, bytes_requested: int | None = None) -> bytes | None:
        """Reads until it gets ``bytes_requested`` number of bytes.
        Waits forever if ``bytes_requested`` is None, you have been warned.
        Returns None if you request 0 bytes like a smartass.
        Does not actually read anything until there is enough bytes available.

        :param bytes_requested: Number of bytes to read before stopping, defaults to None
        :type bytes_requested: int | None, optional
        :return: The requested bytes or None
        :rtype: bytes | None
        """
        if bytes_requested == 0: return None #handles smartasses

        if bytes_requested is None:
            while True:
                await asyncio.sleep(0)
        else:
            while (self.in_waiting < bytes_requested):
                await asyncio.sleep(0)
            
            return super().read(bytes_requested) #At this point this will be instant because all the bytes are there
    
    async def async_read(self, bytes_requested: int | None = None) -> bytes | None:
        """Attempts to get ``bytes_requested`` bytes until it times out.
        On timeout will return any bytes that are available in UART, or None if there aren't any.

        :param bytes_requested: Number of bytes to attempt to read, defaults to None
        :type bytes_requested: int | None, optional
        :return: Available bytes up to length bytes_requested
        :rtype: bytes | None
        """
        #Using wait_for_ms because wait_for likes to break circuitpython REPL
        output = bytearray()
        try:
            #Timeout is reset per character, same as synchronous equivalents
            while len(output) < bytes_requested:
                output.append(await asyncio.wait_for_ms(self.__async_get_byte_forever(), self.timeout * 1000))
        except asyncio.TimeoutError:
            logger.debug("TIMEOUT_REACHED")
            if len(output) < 1: output = None
        
        if output is None:
            logger.debug(f"ASYNC_UART_READ_OUTPUT: {output}")
        else:
            logger.debug(f"ASYNC_UART_READ_OUTPUT: {binascii.hexlify(output)}")
        
        return output

    async def async_read_until_forever(self, bytes_to_match: bytes) -> bytes:
        """Reads UART asynchronously until specified byte sequence is read.
        Actually does read UART while running so do not interrupt this unless you want some garbage left behind.

        :param bytes_to_match: Byte sequence to stop at (included in output)
        :type bytes_to_match: bytes
        :return: Byte sequence that was read
        :rtype: bytes
        """
        output = bytearray()
        while output[-len(bytes_to_match):] != bytes_to_match:
            output.append(await self.__async_get_byte_forever())
        
        logger.debug(f"ASYNC_UART_READ_UNTIL_OUTPUT: {binascii.hexlify(bytes(output))}")
        return bytes(output)

    async def aysnc_read_RTCM3_packet_forever(self) -> bytes:
        """Asynchronously reads an entire RTCM3 packet sequence.
        There is no end marker for this so we read until the start of the next packet and prepend the packet marker (``b'\\xd3\\x00'``).

        :return: RTCM3 bytes
        :rtype: bytes
        """
        output = await self.async_read_until_forever(b'\xd3\x00')
        output = b'\xd3\x00' + output[:-2]

        logger.debug(f"ASYNC_UART_READ_RTCM3_OUTPUT: {binascii.hexlify(bytes(output))}")
        return bytes(output)

    async def async_readline_forever(self) -> bytes:
        """Reads asynchronously until ``\\n`` (included in output).

        :return: Line that was read
        :rtype: bytes
        """
        output = await self.async_read_until_forever(b'\n')

        logger.debug(f"ASYNC_UART_READLINE_OUTPUT: {binascii.hexlify(output)}")
        return output
