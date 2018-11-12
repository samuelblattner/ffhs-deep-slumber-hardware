import csv
from datetime import datetime
import time

from sense_hat import SenseHat

sense = SenseHat()

last_roll = 0.0
last_pitch = 0.0
last_yaw = 0.0

thres = 0.05

record = []
i = 0

endtime = datetime(2018, 9, 25, 12, 30)

while datetime.now() < endtime:
    orient = sense.get_gyroscope_raw()
    roll, pitch, yaw = orient.values()
    diff_roll = abs(last_roll - roll)
    diff_pitch = abs(last_pitch - pitch)
    diff_yaw = abs(last_yaw - yaw)

    # if i == 5:
    #     print('---- Start Movement ----')
    # if i == 15:
    #     print('---- End Movement ----')

    if diff_roll + diff_pitch + diff_yaw > thres:
        record.append((datetime.now(), roll, pitch, yaw, diff_roll, diff_pitch, diff_yaw, sense.get_temperature(), sense.get_humidity()))
        print('MOVEMENT DETECTED! Roll {}, Pitch {}, Yaw {}'.format(last_roll, last_pitch, last_yaw))

    time.sleep(1)
    last_roll, last_pitch, last_yaw = roll, pitch, yaw
    # i += 1

with open('record.csv', 'w', encoding='utf-8') as f:
    csv_handle = csv.DictWriter(f, fieldnames=('timestamp', 'roll', 'pitch', 'yaw', 'd_roll', 'd_pitch', 'd_yaw', 'd_sum', 'thres', 'temp', 'humid'))
    csv_handle.writeheader()

    for rec in record:
        csv_handle.writerow({
            'timestamp': rec[0],
            'roll': rec[1],
            'pitch': rec[2],
            'yaw': rec[3],
            'd_roll': rec[4],
            'd_pitch': rec[5],
            'd_yaw': rec[6],
            'd_sum': rec[4] + rec[5] + rec[6],
            'thres': thres,
            'temp': rec[7],
            'humid': rec[8],
        })

