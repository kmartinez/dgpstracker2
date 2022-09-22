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
- [x] Fix the direction of Q1, Q3, Q5
- [x] Isolate BQ24074 output from the input of LTC3130-1 and LTC3113
- [x] Remove JST battery terminal
- [x] Swap Solar input screw terminal footprint with a ~~standard~~ push-click one
- [x] Make PJ-031D face away from board
- [x] Swap VS1 and VS2
- [x] Rename ambiguous signal names
- [x] Power tracks width increased from 10 to 16 mil, where appropriate
- [x] Added more pins for input/output signals for probing when jumpered
- [x] Added two more outputs: 
  - one for 5V GSM
  -  one for 3.3V GSM logic
- [x] Added two versions of power switches for consumption comparison:
  - one with DMG/DMP mosfets
  - one with ~~DMC3028LSDX-13~~ IRF7319 dual cmos
- [x] Add pads for Harwin RFI cans 
	- 30mm X 30mm or 50mm X 25mm for LTC3113 section 
	- 30mm X 25mm for LTC3130-1 section


### Ordered:
- DMG3414U N-channel MOSFET - unavailable at mouser!
- DMP2045U P-channel MOSFET
- IRF7319 Dual P/N-channel MOSFET pair

### Notes/remaining issues:
-  Harwin RFI can pads are only there for future design reference,
 the dimensions of the latest version's pads are not compatible with any of the available models