import busio
import microcontroller
import asyncio
from debug import *
import time

class AsyncUART(busio.UART):
    async_timeout: int
    __dangerous_output: bytearray #If you use this abomination MAKE SURE TO INITIALIZE IT FIRST

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
        ):
        super().__init__(tx, rx, baudrate=baudrate, bits=bits, parity=parity, timeout=0, stop=stop, receiver_buffer_size=receiver_buffer_size)
        self.async_timeout = timeout
    
    async def __async_get_byte(self):
        '''Waits for a received byte and returns it.'''
        output = None
        while output is None:
            output = super().read(1)
            if output is None:
                await asyncio.sleep(0)
        #debug("READ_BYTE:", output[0])
        return output[0] #read returns a byte array
    
    async def __async_read_forever(self):
        '''Reads UART forever. ONLY for use with async_read_with_timeout'''
        self.__dangerous_output = bytearray()
        while True:
            self.__dangerous_output.append(await self.__async_get_byte())

    async def async_read(self, bytes_requested: int | None = None) -> bytes:
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
    
    async def async_read_with_timeout(self, bytes_requested: int | None = None) -> bytes | None:
        '''Attempts to get `bytes_requested` bytes until it times out.
        Returns whatever bytes it retrieved or None if nothing was retrieved'''
        #Using wait_for_ms because wait_for likes to break circuitpython REPL
        output = None
        try:
            if bytes_requested is None:
                output = await asyncio.wait_for_ms(self.__async_read_forever(), self.async_timeout * 1000)
            else:
                output = await asyncio.wait_for_ms(self.async_read(bytes_requested), self.async_timeout * 1000)
        except:
            debug("TIMEOUT_REACHED")
            if len(self.__dangerous_output) < 1: return None
            else: return bytes(self.__dangerous_output)
        
        return output

    async def async_readline(self):
        '''Reads asynchronously until `\n` (included in output)
        ***DOES NOT TIMEOUT***'''
        output = bytearray()
        byte = await self.__async_get_byte()
        #debug("RAW_READLINE_BYTE:", byte)
        while True:
            output.append(byte)
            if byte == b'\n'[0]:
                break
            byte = await self.__async_get_byte()
        
        return bytes(output)
    
    def readline(self):
        output = bytearray()
        start_time = time.time()
        while True:
            byte = super().read(1)
            if byte is not None:
                #debug("RAW_SYNC_BYTE:", byte)
                output.append(byte[0])
                if (byte == b'\n'):
                    break;
            if time.time() - start_time > self.async_timeout:
                break
        
        debug("READLINE_SYNC_OUTPUT: ", output)
        if len(output) > 0:
            return bytes(output)
        else:
            return None
