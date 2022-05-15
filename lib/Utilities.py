import hashlib
from uuid import uuid4


def get_integer(msg="Number: ", wrng_msg="Invalid Input", defaultVal=None):
    try:
        i = input(msg)
        if defaultVal is not None and i == "":
            return defaultVal
        i = int(i)
    except ValueError:
        print(wrng_msg)
        return get_integer(msg, wrng_msg)
    else:
        return i


def uuid():
    return str(uuid4()).replace('-', '')


def get_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()
