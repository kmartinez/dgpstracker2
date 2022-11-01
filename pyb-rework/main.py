base = True

if __name__ == "__main__":
    if base:
        exec(open('./Base.py').read())
    else:
        exec(open('./Rover.py').read())