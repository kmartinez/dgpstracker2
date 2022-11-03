base = True

if __name__ == "__main__":
   input()
   if base:
      print("I'm a base station!\r\n")
      exec(open('./Base.py').read())
   else:
      print("I'm a rover!\r\n")
      exec(open('./Rover.py').read())