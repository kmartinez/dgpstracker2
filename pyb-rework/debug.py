from config import *

def debug(
    *values: object,
) -> None:
    '''Prints if debugging is on'''
    if DEBUG["LOGGING"]:
        print(*values)