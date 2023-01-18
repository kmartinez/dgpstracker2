import board, digitalio, time, storage


button_record = digitalio.DigitalInOut(board.D21)
button_record.switch_to_input(pull=digitalio.Pull.UP)   #switch_to_input will wait until it detects an input from the button


#create flag variables


#if switch pin is connected to ground CircuitPython can write to the drive
storage.remount("/", not(button_record.value))
