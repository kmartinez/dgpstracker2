class RollingAverage:
    circularBuffer: list[int | float]
    max_length: int

    def __init__(self, max_length: int) -> None:
        self.circularBuffer = []
        self.max_length = max_length
    
    def append(self, value: int | float) -> None:
        """Append a sample to the rolling average

        :param value: Value of sample
        :type value: int | float
        """
        self.circularBuffer.append(value)
        if len(self.circularBuffer) > self.max_length:
            del(self.circularBuffer[0])
    
    def mean(self) -> float:
        """Calculates the current mean

        :return: Mean value of current samples
        :rtype: float
        """
        return sum(self.circularBuffer) / len(self.circularBuffer)
    
    def sd(self) -> float:
        """Calculates the current standard deviation

        :return: Standard deviation of current samples
        :rtype: float
        """
        cached_length = len(self.circularBuffer)
        cached_mean = self.mean()
        diff_to_means = map(lambda x: x - cached_mean, self.circularBuffer) #This is an iterable, not a list. Still works with sum but you've been warned
        variance = sum(map(**2, diff_to_means)) / cached_length
        return variance**0.5