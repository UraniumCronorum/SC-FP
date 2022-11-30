
def readInt():
    user = int(input('<readInt> int:'))
    while not isinstance(user, int):
        user = int(input('<readInt> try again:'))
    return user

