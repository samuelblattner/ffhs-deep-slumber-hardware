"""
===
Main entry point for Deep Slumber Hardware Routines.
===

"""
from outpost.enum import MessageType

__author__ = 'Samuel Blattner'
__version__ = '1.0.0'


from logger.logger import Logger
from orchestra.orchestra import Orchestra
from outpost.outpost import Outpost
from risenshine.risenshine import RiseNShine


# 1. Create Outpost for server communicatino
outpost = Outpost()

# 2. Create logger for logging
logger = Logger(consumers=[outpost])

# 3. Create orchestra for sensor/actuator management
orchestra = Orchestra(logger=logger)

# 4. Create RiseNShine for waking procedures
# and sign up as listener to incoming messages from server
risenshine = RiseNShine(orchestra=orchestra, logger=logger)
outpost.register_listener(risenshine, [MessageType.SETTINGS])

# Once all the setup is done we can start the
# message loop. This loop is blocking and will run forever.
# Connection failures will be handled within the connect() method.
outpost.connect()
