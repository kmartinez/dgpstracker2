### Issues found on version 1 of evalboard:
- P-channel MOSFETs Q1, Q3, Q5 are in reverse direction
- Outputs of BQ24074 are not isolated from input of LTC3130-1 and LTC3113
- Battery 2mm JST footprint requires special Sparkfun sockets
- Solar input header does not fit standard 3.5mm screw terminals
- PJ-031D is the wrong way around (facing the inside of the board)
- PJ-031D solar input jack is not long enough, but otherwise locks into the solar connector OK
- VS1 and VS2 of LTC3130-1 is the other way around (GND and VCC) giving 5V instead of 3.3V
- Signal names create confusion

### Improvements/additions in next version:
- Fix the direction of Q1, Q3, Q5
- Isolate BQ24074 output from the input of LTC3130-1 and LTC3113
- Remove JST battery terminal
- Swap Solar input screw terminal with a standard one
- Make PJ-031D face away from board
- Swap VS1 and VS2
- Rename ambiguous signal names
- Add two more outputs: 
  - one for 5V GSM
  -  one for 3.3V GSM logic
- Add two versions of power switches for consumption comparison:
  - one with DMG/DMP mosfets
  - one with DMC3028LSDX-13 dual cmos 

