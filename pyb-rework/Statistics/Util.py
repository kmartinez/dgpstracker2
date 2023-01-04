"""Utility functions to calculate various statistical analysis information
compatible with DecimalNumbers
"""

def mean(buffer):
        """Calculates the current mean

        :return: Mean value of current samples
        :rtype: float
        """
        return sum(buffer) / len(buffer)
    
def square_for_var(x):
    try:
        return x**2
    except:
        return 0

def var(buffer):
    """Calculates the current standard deviation

    :return: Standard deviation of current samples
    :rtype: float
    """
    
    cached_length = len(buffer)
    cached_mean = mean(buffer)
    print("Buffer:", buffer)
    diff_to_means = map(lambda x: x - cached_mean, buffer) #This is an iterable, not a list. Still works with sum but you've been warned
    print("diff_to_means:", diff_to_means)
    return sum(map(square_for_var, diff_to_means)) / cached_length
