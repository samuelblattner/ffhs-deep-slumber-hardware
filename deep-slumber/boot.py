from logger.logger import Logger
from orchestra.orchestra import Orchestra
from outpost.outpost import Outpost
from outpost.exceptions import OutpostConnectionException
from risenshine.risenshine import RiseNShine


try:
    outpost = Outpost()
except OutpostConnectionException:
    exit(1)

outpost.connect()
settings = outpost.getSettings()
logger = Logger()


orchestra = Orchestra()

risenshine = RiseNShine()