import config

def debug(
    *values: object,
) -> None:
    '''Prints if debugging is on'''
    if config.DEBUG["LOGGING"]:
        print(*values)