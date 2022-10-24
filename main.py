from asyncio.windows_events import NULL
import sys
import sqlite3
import time
import random

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

def start_session(uid):
    # starts a session for the user

    global connection, cur

    current_date = time.strftime("%Y-%m-%d %H:%M:%S")

    # check if this session is the first one added
    cur.execute("SELECT COUNT(*) FROM sessions")
    ses_count = cur.fetchone()

    if ses_count == 0:
        sno = 1
    else:
        # get unique sno by adding 1 to the last sno added
        cur.execute("SELECT sno FROM sessions")
        snos = cur.fetchall()
        largest_sno = snos[len(snos)-1][0]
        sno = largest_sno + 1

    new_session = """
                    INSERT INTO sessions(uid, sno, start, end)
                    VALUES (:userid, :sesno, :stime, NULL)
                  """

    cur.execute(new_session, {"userid": uid, "sesno": sno, "stime": current_date})
    
    print("===================================")
    print("SESSION {sessionno} STARTED".format(sessionno=sno))
    print("===================================")

    connection.commit()

def similar_words(dbword, usearch):
    count = 0
    counted_words = []

    dbword = dbword.split()
    usearch = usearch.split()

    for sword in dbword:
        if sword in usearch and sword not in counted_words:
            counted_words.append(sword)
            count += 1

    return count

def print_sp_page(pages, page_no):
    page = pages[page_no]

    print("===================================")
    print("-----------------------------------")
    print("Page Number: " + page_no)
    print("-----------------------------------")

    counter = 0
    for result in page:
        print("Result Number: " + page_no + "." + counter)
        print("Type: " + result[1] + ", Title: " + result[3] + ", Duration: " + result[3] + ", ID: " + result[0])
    print("===================================")

def search_sp():
    # allows the user to search for a song or playlist
    global connection, cur
    connection.row_factory = sqlite3.Row
    print("===================================")
    print("Searching for songs and playlists")
    print("===================================")

    keywords = input("Please enter your search: ")

    get_ps = """
                WITH ps_results(id, type, title, duration, sim_count) as (
                SELECT sid, 'Song' as type, s.title, duration, sim_words(title, :usearch) as sim_count
                FROM songs
                WHERE sim_count > 0
                UNION
                SELECT p.pid, 'Playlist' as type, p.title, sum(s.duration), sim_words(p.title, :usearch) as sim_count
                FROM playlists p, songs s, plinclude pi
                WHERE sim_count > 0
                and p.pid = pi.pid
                and pi.sid = s.sid
                GROUP BY p.pid, p.title
                )
                SELECT * 
                FROM ps_results
                ORDER BY sim_count DESC
                """

    cur.execute(get_ps, {"usearch": keywords})
    ps_results = cur.fetchall()

    # put results into pages
    ps_pages = []
    counter = 0
    while (counter != len(ps_results)-1):
        if len(ps_results - counter >= 5):
            while(counter % 5 != 0):
                page = []
                page.append(ps_results[counter])
                counter += 1
            ps_pages.append(page)
        else:
            while (counter != len(ps_results)-1):
                page = []
                page.append(ps_results[counter])
                counter += 1
            ps_pages.append(page)

    # print first results
    current_page = 0
    print_sp_page(ps_pages, current_page)

    # print next pages
    next = 'n'
    while next == 'n':
        next = input("If you would like to see the next page, enter 'y'. If not, enter 'n': ")
        if next == 'y':
            current_page += 1
            print_sp_page(ps_pages, current_page)

    user_choice = input("If you would like to select a result, enter with the format [Page Number].[Result Number]. If not, enter 'n': ")

    if user_choice == 'n':
        home()
    else:
        choice = user_choice.split(".")
        selected_page = ps_pages[]


def search_artist():
    # allows the user to search for an artist
    global connection, cur
    print("===================================")
    print("Searching for artists")
    print("===================================")

    keyword = input("Please enter your search: ")

    for word in keyword:
        find_artist = """
                      SELECT * FROM artists
                      """
        

def end_session(uid):
    # allows the user to end their session
    global connection, cur

    current_date = time.strftime("%Y-%m-%d %H:%M:%S")

    print("===================================")
    print("SESSION ENDED")
    print("===================================")

    update_session = """
                    UPDATE sessions
                    SET end = :curtime
                    WHERE uid = :userid
                    and end = NULL
                   """
    cur.execute(update_session, {"userid": uid, "curtime": current_date})
    connection.commit()

def home(uid):
    print("===================================")
    print("Welcome to the home screen!")
    print("""
            Enter 1 to start a session
            Enter 2 to search for songs and playlists
            Enter 3 to search for artists
            Enter 4 to end the session
            Enter 5 to logout
        """)
    print("===================================")
    user_choice = input("Please enter your choice: ")

    if user_choice == "1":
        start_session(uid)
    elif user_choice == "2":
        search_sp()
    elif user_choice == "3":
        search_artist()
    elif user_choice == "4":
        end_session(uid)
    elif user_choice == "5":
        login()
    else:
        print("Invalid input.")
        home()

def login():
    # login screen to retrieve account and detect if account is user, artist, or both

    account_id = input("Please enter your id: ")
    password = input("Please enter your password: ")

def main():
    global connection, cur
    connection.create_function("sim_words", 2, similar_words)
    #momo :()
    # retrieve database from command line
    db = sys.argv[1]

    # retrieve path to connect to
    path = "./{database}".format(database=db)
    connect(path) 

    # main program
    login()
    home()
    
    # close connection and finish program
    connection.commit()
    connection.close()
    return

if __name__ == "__main__":
    main()
