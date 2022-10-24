import sys
import sqlite3

connection = None
cur = None

def connect(path):
    # connect to sqlite

    global connection, cur
    connection = sqlite3.connect(path)
    cur = connection.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    connection.commit()
    return

def login():
    # login screen to retrieve account and detect if account is user, artist, or both

    account_id = input("Please enter your id: ")
    password = input("Please enter your password: ")

    # checking if account is artist
    cur.execute("Select aid From artists;")
    artists = cur.fetchall()
    artist = False
    if account_id in artists:
        artist = True
    # checking if account is user 
    cur.execute("Select uid from users;")
    users = cur.fetchall()
    user = False
    if account_id in users and account_id not in artists:
        user = True
        return account_id
    
    if user and artist:
        prompt = input("Do you want to login as an artist or a user? Please enter a or u: ")
    
    if account_id not in users:
        new_uid = input("Please enter a new unique uid: ")
        while new_uid not in users:
            new_uid = input("Please enter a new unique uid: ")
        # password
        # name
    return new_uid
        



def main():
    global connection, cur

    
    # retrieve database from command line
    db = sys.argv[1]

    # retrieve path to connect to
    path = "./{database}".format(database=db)
    connect(path) 

    # main program
    login()
    
    # close connection and finish program
    connection.commit()
    connection.close()
    return

if __name__ == "__main__":
    main()
