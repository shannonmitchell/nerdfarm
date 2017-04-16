#!/usr/bin/python

import sys
import time
import signal
import threading
import RPi.GPIO as GPIO
import datetime

##########################
# GPIO pin definitions
##########################

# These were mapped and tested on a raspberry pi model B
GROW_LIGHT_PIN           = 17
PUMP_RELAY_PIN           = 18
MOISTER_PROBE_ENABLE_PIN = 24
MOISTER_PROBE_INPUT_PIN  = 23



###################################################################
# Method to clean up the system when catching a SIGTERM or SIGING
###################################################################
def cleanStop(signum, frame):

    print "Cleaning and shutting the system down"

    # Turn the light off
    GPIO.output(GROW_LIGHT_PIN, GPIO.LOW)

    # Make sure the water is off
    GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)

    # Disable the moister probe pin
    GPIO.output(MOISTER_PROBE_ENABLE_PIN, GPIO.LOW)

    # exit(make sure thread.daemon is enabled on your child threds
    #      or the process will hang)
    sys.exit(0)


#############################################
# Thread method to start/stop the grow light 
#############################################
def manageLight():

    print "Starting the manageLight thread\n"

    # Keep track of the light status. 
    lightOn = 0

    # Set up a loop to check and enable/disable the light as needed
    while 1:

        # Pull the current time for comparison
        now = datetime.datetime.now()

        # Trigger if the time falls between the thresholds
        if datetime.time(15,00) <= now.time() < datetime.time(23,59):

            # Only turn on the light once within the threshold
            if lightOn == 0:
                print "Starting grow light"
                GPIO.output(GROW_LIGHT_PIN, GPIO.HIGH)
                lightOn = 1
        else:

            # Only stop the light once after exiting the threshold
            if lightOn == 1:
                print "Stopping the grow light"
                GPIO.output(GROW_LIGHT_PIN, GPIO.LOW)
                lightOn = 0

        # sleep for 10 minutes
        time.sleep(600)


#############################################################################
# Thread method to check the soil moister level and depsense water as needed
#############################################################################
def manageWater():

    print "Starting the manageWater thread\n"

    # Set up a loop to check the moister level and depsense water
    while 1:

        # Enable the probe just long enough to check the soil.
        # If left enabled reviews show that it causes the probes
        # to corrode quicker.
        GPIO.output(MOISTER_PROBE_ENABLE_PIN, GPIO.HIGH)

        # Give the probe a little time before checking
        time.sleep(5)

        # The moister board will give us a high if its below the threshold
        water_output = GPIO.input(MOISTER_PROBE_INPUT_PIN)

        # Just putting in a small timer before shutting the probe off
        time.sleep(5)

        # Remove power from the probe again to prevent corrosion
        GPIO.output(MOISTER_PROBE_ENABLE_PIN, GPIO.LOW)
        
        # A setting of 0 shows good water value
        if water_output != 0:
            
            print "Water is low. Pumping water in for 5 seconds"
            GPIO.output(PUMP_RELAY_PIN, GPIO.HIGH)
            time.sleep(5)
            GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)

        # Sleep an hour before the next check
        # Keep this fairly high to allow the soil to soak up the moister. 
        # If set too low the soil around the probe will not have soaked
        # up the moister and the pot will overflow.
        time.sleep(3600)


###################################################################################
# Main method to spin up the various threads need to manage the sensors and relays
# for automation.
###################################################################################
def main():

    # Set up signal handlers
    # make sure you set threads '.daemon' attributes to True or the process hangs.
    signal.signal(signal.SIGTERM, cleanStop)
    signal.signal(signal.SIGINT, cleanStop)


    # Init the board using BCM
    GPIO.setmode(GPIO.BCM)

    # Set proper in/outputs
    GPIO.setwarnings(False)
    GPIO.setup(GROW_LIGHT_PIN, GPIO.OUT)
    GPIO.setup(PUMP_RELAY_PIN, GPIO.OUT)
    GPIO.setup(MOISTER_PROBE_ENABLE_PIN, GPIO.OUT)
    GPIO.setup(MOISTER_PROBE_INPUT_PIN, GPIO.IN)

    # Initiate pins.
    GPIO.output(GROW_LIGHT_PIN, GPIO.LOW)
    GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
    GPIO.output(MOISTER_PROBE_ENABLE_PIN, GPIO.LOW)

    # Start the light controller thread
    light_thread = threading.Thread(name='LightThread', target=manageLight)
    light_thread.daemon = True
    light_thread.start()

    # Start the water management thread
    water_thread = threading.Thread(name='WaterThread', target=manageWater)
    water_thread.daemon = True
    water_thread.start()

    # Wait here for a control signal.
    signal.pause()
     
    # Clear pins.
    GPIO.output(GROW_LIGHT_PIN, GPIO.LOW)
    GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
    GPIO.output(MOISTER_PROBE_ENABLE_PIN, GPIO.LOW)


if __name__ == '__main__':
  main()
