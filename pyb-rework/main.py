base = True

if __name__ == "__main__":
   #input()
   if base:
      print("I'm a base station!")
      exec(open('./Base.py').read())
   else:
      print("I'm a rover!")
      exec(open('./Rover.py').read())