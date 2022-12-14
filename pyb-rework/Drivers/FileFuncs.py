import os
import storage

LOGS_PATH = "Logs/log.txt"
DATA_PATH = "Data/data.txt"
FILE_DELIMITER = "|||"
UNSENT = "UNSENT"
SENT = "SENT"
SENDING = "SENDING"

def log(msg):
    with open(LOGS_PATH,'a') as lp:
        lp.write(str(msg)+"\n")
        lp.close()

def append_data(data):
    with open(DATA_PATH, 'a') as dp:
        dp.write(data)
        dp.close()

def store_data(data,status):
    print("Writing:",str(data) + FILE_DELIMITER + str(status) + "\n")
    append_data(str(data) + FILE_DELIMITER + str(status) + "\n")

def read_data(status_tag):
    with open(DATA_PATH, 'r') as dp:
        out = []
        position = 0
        while len(line := dp.readline()) > 0:
            #print("LINE:",line)
            #print("SPLIT LINE:", line.split(FILE_DELIMITER))
            data,status = line.split(FILE_DELIMITER)
            if status[-1] == "\n":
                status = status[:-1]

            if status == status_tag:
                out.append([data,position])

            position += 1

        dp.close()
        return out

def change_line_status(pos,new_status):
    with open(DATA_PATH, 'r') as dp_in:
        for i in range(pos):
            dp_in.readline()
        loc = dp_in.tell()

        # Get remaining data
        line = dp_in.readline()
        data = line.split("|||")[0]
        remaining_data = dp_in.read()
        dp_in.close()

    with open(DATA_PATH, 'w') as dp_out:
        dp_out.seek(loc)
        dp_out.write("")
        dp_out.close()

    with open(DATA_PATH, 'a') as dp_out:
        dp_out.write(data+FILE_DELIMITER+new_status+"\n")
        dp_out.write(remaining_data)
        dp_out.close()

def del_line_in_data(position):
    with open(DATA_PATH,'r') as dp_in:
        data = dp_in.read().splitlines(True)
        dp_in.close()
    with open(DATA_PATH, 'w') as dp_out:
        dp_out.write("")
        dp_out.close()
    with open(DATA_PATH, 'a') as dp_out:
        for i in range(len(data)):
            if i != position:
                dp_out.write(data[i])
        dp_out.close()
