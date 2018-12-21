from logger.logger import Logger
from orchestra.orchestra import Orchestra
from outpost.outpost import Outpost
from outpost.exceptions import OutpostConnectionException
from risenshine.risenshine import RiseNShine

try:
    try:
        outpost = Outpost()
    except OutpostConnectionException:
        exit(2)
    settings = outpost.getSettings()
    logger = Logger([outpost])
    orchestra = Orchestra(settings, logger)
    risenshine = RiseNShine(orchestra, logger)
    outpost.set_waking_oerator(risenshine)

    outpost.connect()
except Exception as e:
    print(e, file=open('error.txt', 'a'))
