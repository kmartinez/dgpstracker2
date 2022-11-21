import ulab.numpy as np

class StatsBuffer:
    circularBuffer: list[float]
    max_length: int

    def __init__(self, max_length: int) -> None:
        self.circularBuffer = []
        self.max_length = max_length
    
    def append(self, value: int | float) -> None:
        """Append a sample to the rolling average

        :param value: Value of sample
        :type value: int | float
        """
        if value is not float:
            value = float(value)
        self.circularBuffer.append(value)
        if len(self.circularBuffer) > self.max_length:
            del(self.circularBuffer[0])

    #Allows iteration over the buffer
    def __iter__(self):
        return self.circularBuffer.__iter__()