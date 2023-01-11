"""Module to help with processing maths over a rolling sample period
"""

import ulab.numpy as np
from mpy_decimal import *

class StatsBuffer:
    """Class to help with making a rolling average of information
    """
    circularBuffer: list[DecimalNumber]
    max_length: int

    def __init__(self, max_length: int) -> None:
        self.circularBuffer = []
        self.max_length = max_length
    
    def append(self, value: int | DecimalNumber) -> None:
        """Append a sample to the rolling average

        :param value: Value of sample
        :type value: int | float
        """
        if type(value) is float:
            value = DecimalNumber(str(value))
        elif type(value) is not DecimalNumber:
            value = DecimalNumber(value)
        self.circularBuffer.append(value)
        if len(self.circularBuffer) > self.max_length:
            del(self.circularBuffer[0])

    #Allows iteration over the buffer
    def __iter__(self):
        return self.circularBuffer.__iter__()