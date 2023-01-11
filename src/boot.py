"""Executed before main module by CircuitPython.
Configures on-board storage for read/write capabilities
"""

import board, digitalio, storage


switch = digitalio.DigitalInOut(board.A4)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

#if switch pin is connected to ground CircuitPython can write to the drive
storage.remount("/", False, disable_concurrent_write_protection = True)