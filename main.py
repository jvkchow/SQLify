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
    cur.execute("Select uid from users;")
    users = cur.fetchall()

    cur.execute("Select aid From artists;")
    artists = cur.fetchall()

    answer = input("Do you want to make a new account (n) or login (l)? Enter n or l:")
    while answer.lower() != "n" and answer.lower() != "l":
        answer = input("Do you want to make a new account (n) or login (l)? Enter n or l:")

    # adding new user
    if answer.lower() == 'n':
        new_uid = input("\nPlease enter a unique id: ")
        while new_uid in users:
            new_uid = input("\nThis id is already being used, please enter a unique id: ")
        name = input("\nPlease enter your name: ")
        password = input("\nPlease enter a new password: ")

        cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})

    
    # logging in
    if answer.lower() == 'l':
        id = input("\nPlease enter your id: ")

        if id in users and id not in artists:
            password = input("\nPlease enter your password: ")
            cur.execute("Select pwd from users where uid = :id;", {"id": id})
            pwd = cur.fetchone()
            while password != pwd:
                password = input("\nIncorrect password. Please try again.")
            
        elif id in artists and id not in users:
            password = input("\nPlease enter your password: ")
            cur.execute("Select pwd from artists where aid = :id;", {"id": id})
            pwd = cur.fetchone()
            while password != pwd:
                password = input("\nIncorrect password. Please try again.")
            
        elif id in artists and id in users:
            log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
            while log_choice.lower() not in ['u', 'a']:
                log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
            if log_choice.lower() == 'u':
                password = input("\nPlease enter your password: ")
                cur.execute("Select pwd from users where uid = :id;", {"id": id})
                pwd = cur.fetchone()
                while password != pwd:
                    password = input("\nIncorrect password. Please try again.")
            elif log_choice.lower() == 'a':
                password = input("\nPlease enter your password: ")
                cur.execute("Select pwd from artists where aid = :id;", {"id": id})
                pwd = cur.fetchone()
                while password != pwd:
                    password = input("\nIncorrect password. Please try again.")
                    
        elif id not in artists and id not in users: 
            print("\nYou have to make a new user account")
            new_uid = input("\nPlease enter a unique id: ")
            while new_uid in users:
                new_uid = input("\nThis id is already being used, please enter a unique id: ")
            name = input("\nPlease enter your name: ")
            password = input("\nPlease enter a new password: ")
            cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})
        
        return id


            




        



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
