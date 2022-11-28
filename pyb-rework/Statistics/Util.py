def mean(buffer) -> float:
        """Calculates the current mean

        :return: Mean value of current samples
        :rtype: float
        """
        return sum(buffer) / len(buffer)
    
def sd(buffer) -> float:
    """Calculates the current standard deviation

    :return: Standard deviation of current samples
    :rtype: float
    """
    cached_length = len(buffer)
    cached_mean = mean(buffer)
    diff_to_means = map(lambda x: x - cached_mean, buffer) #This is an iterable, not a list. Still works with sum but you've been warned
    variance = sum(map(**2, diff_to_means)) / cached_length
    return variance**0.5