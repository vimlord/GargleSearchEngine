import datetime

# I wanted to have logging with an ISO timestamp

def log(*args):
    print(datetime.datetime.now().isoformat(), *args)

