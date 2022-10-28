import Base
import time

global GPS


if __name__ == "__main__":
	device = Base

	# Get GPS data

	# send_command sends a NMEA commands to the GPS
	# TODO: replace with correct commands for uBlox GPS
	device.GPS.send_command(b'UBX-CFG-CODE,DATA')
	while True:
		device.GPS.update()
		if not device.GPS.has_fix:
			print('Waiting for fix...')
			continue
		print('=' * 40)  # Print a separator line.
		print('Latitude: {0:.6f} degrees'.format(device.GPS.latitude))
		print('Longitude: {0:.6f} degrees'.format(device.GPS.longitude))
		break