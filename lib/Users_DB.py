from lib.Utilities import get_hash


def authenticate_user(usr_id):
    f = open('lib/users', 'r')
    data = f.readlines()
    data = [i.strip() for i in data]
    if get_hash(usr_id) in data:
        return 1
    return 0


def add_user(usr_id):
    f = open('lib/users', 'a')
    f.writelines([get_hash(usr_id), "\n"])
