import busio
from busio import Parity
import microcontroller
from typing import Optional
import asyncio

class AsyncUART(busio.UART):
    timeout: int
    __dangerous_output: bytearray #If you use this abomination MAKE SURE TO INITIALIZE IT FIRST

    def __init__(
        self,
        tx: microcontroller.Pin,
        rx: microcontroller.Pin,
        *,
        baudrate: int = 9600,
        bits: int = 8,
        parity: Optional[Parity] = None,
        stop: int = 1,
        timeout: int = 1,
        receiver_buffer_size: int = 64,
        ):
        super().__init__(tx, rx, baudrate=baudrate, bits=bits, parity=parity, timeout=0, stop=stop, receiver_buffer_size=receiver_buffer_size)
        self.timeout = timeout
    
    async def __async_get_byte(self):
        '''Waits for a received byte and returns it.'''
        output = None
        while output is None:
            output = super().read(1)
            if output is None:
                asyncio.sleep(0)
        return output[0] #read returns a byte array
    
    async def __async_read_forever(self):
        '''Reads UART forever. ONLY for use with async_read_with_timeout'''
        self.__dangerous_output = bytearray()
        while True:
            self.__dangerous_output.append(await self.__async_get_byte())

    async def async_read(self, bytes_requested: Optional[int] = None) -> bytes:
        '''Reads until it gets `bytes_requested` number of bytes.
        If bytes is not specified it waits until *something* arrives,
        then reads everything that is available (even if it's not finished receiving).
        ***DOES NOT TIMEOUT***'''
        if bytes == 0: return None #handles smartasses

        self.__dangerous_output = bytearray() #Put into there in case of timeouts so we can extract what we have
        #Wait for first byte

        byte = await self.__async_get_byte()
        i = 1
        while byte is not None:
            self.__dangerous_output.append(byte)
            if bytes_requested is None: byte = super().read(1)
            elif i < bytes_requested:
                byte = await self.__async_get_byte()
                i += 1
            else: byte = None
        
        return bytes(self.__dangerous_output)
    
    async def async_read_with_timeout(self, bytes_requested: Optional[int] = None) -> Optional[bytes]:
        '''Attempts to get `bytes_requested` bytes until it times out.
        Returns whatever bytes it retrieved or None if nothing was retrieved'''
        #Using wait_for_ms because wait_for likes to break circuitpython REPL
        try:
            if bytes_requested is None:
                await asyncio.wait_for_ms(self.__async_read_forever(), self.timeout * 1000)
            else:
                return await asyncio.wait_for_ms(self.async_read(bytes_requested), self.timeout * 1000)
        except TimeoutError:
            if len(self.__dangerous_output < 1): return None
            else: return bytes(self.__dangerous_output)

    