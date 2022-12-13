LOGS_PATH = "Logs/log.txt"
DATA_STORE = "Data/data.txt"
FILE_DELIMITER = "|||"
UNSENT = "UNSENT"
SENT = "SENT"

def log(msg):
    with open(LOGS_PATH) as lp:
        lp.write(msg,"\n")

def store_data(data,status):
    with open(DATA_STORE) as dp:
        dp.write(str(data) + FILE_DELIMITER + str(status) + "\n")

def read_data(status_tag):
    with open(DATA_STORE) as dp:
        while (line := dp.readline()) is not None:
            data,status = line.split(FILE_DELIMITER)
            if status == status_tag:
                return data
        return None

