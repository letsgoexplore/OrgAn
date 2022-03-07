import re
import sys
import time

print("Config: {}".format(sys.argv[1]))
with open(sys.argv[1], 'r') as f:
    s = f.read()
    avg = 0
    for i in range(10):
        m = re.search(
            r'\[.*([0-9]{2,2}):([0-9]{2,2}):([0-9]{2,2})\.([0-9]{2,3})Z INFO  organ::client\] Round 1.', s)
        time1 = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + \
            int(m.group(3)) + int(m.group(4)) / 1000
        time2 = 0
        mm = re.finditer(
            r'\[.*([0-9]{2,2}):([0-9]{2,2}):([0-9]{2,2})\.([0-9]{2,3})Z INFO  organ::client\] Received ServerBulkMessage.', s)
        for m in mm:
            time2 = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + \
                int(m.group(3)) + int(m.group(4)) / 1000
    print("Avg round time: {}s.".format(round((time2 - time1) / 100, 3)))