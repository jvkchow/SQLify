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
