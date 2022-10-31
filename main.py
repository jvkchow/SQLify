from asyncio.windows_events import NULL
import sys
import sqlite3
import time

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

    current_date = time.strftime("%Y-%m-%d")

    # check if this session is the first one added
    cur.execute("SELECT COUNT(*) FROM sessions;")
    ses_count = cur.fetchone()
    if ses_count[0] == 0:
        sno = 1
    else:
        # get unique sno by adding 1 to the last sno added
        cur.execute("SELECT sno FROM sessions;")
        snos = cur.fetchall()
        largest_sno = snos[len(snos)-1][0]
        sno = largest_sno + 1

    new_session = """
                    INSERT INTO sessions(uid, sno, start, end)
                    VALUES (:userid, :sesno, :stime, NULL);
                  """

    cur.execute(new_session, {"userid": uid, "sesno": sno, "stime": current_date})
    
    print("===================================")
    print("SESSION {sessionno} STARTED".format(sessionno=sno))
    print("===================================")

    home(uid)

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

def print_page(pages, page_no):
    page = pages[page_no]

    print("===================================")
    print("-----------------------------------")
    print("Page Number: " + str(page_no))
    print("-----------------------------------")

    counter = 0
    for result in page:
        print("Result Number: " + str(page_no) + "." + str(counter))
        print("Type: " + result[1] + ", Title: " + result[2] + ", Duration: " + str(result[3]) + ", ID: " + str(result[0]))
        counter += 1
    print("===================================")

def select_song(song):
    # actions that occur when you select a song
    print("===================================")
    print("SELECTED SONG: " + song[2])
    print("===================================")

def select_playlist(playlist):
    # actions that occur when you select a playlist
    print("===================================")
    print("SELECTED PLAYLIST: " + playlist[2])
    print("===================================")

def select_artist(artist):
    # actions that occur when you select a playlist
    print("===================================")
    print("SELECTED PLAYLIST: " + artist[2])
    print("===================================")

def format_page(results):
    # puts results into pages
    pages = []
    counter = 0
    if len(results) <= 0:
        print("\nThere are no results that match your search.")
        return pages

    while counter != len(results):
        if len(results) - counter >= 5:
            page = []
            page_count = 0
            while page_count != 5:
                page.append(results[counter])
                counter += 1
                page_count += 1
            pages.append(page)
        else:
            page = []
            while counter != len(results):
                page.append(results[counter])
                counter += 1
            pages.append(page)
    return pages

def display_pages(pages):
    # print first results
    current_page = 0
    print_page(pages, current_page)
    
    # print next pages
    while current_page != len(pages) - 1:
        next = input("If you would like to see the next page, enter 'y'. If not, enter 'n': ")
        if next == 'y':
            current_page += 1
            print_page(pages, current_page)
        elif next == 'n':
            break
        else:
            print("Invalid Input. Page searching terminated.")
            break

    user_choice = input("If you would like to select a result, enter with the format [Page Number].[Result Number]. If not, enter 'n': ")

    if user_choice == 'n':
        return
    else:
        choice = user_choice.split(".")
        selected_page = pages[int(choice[0])]
        selected_result = selected_page[int(choice[1])]

        if selected_result[1] == "Song":
            select_song(selected_result)
        elif selected_result[1] == "Playlist":
            select_playlist(selected_result)
        elif selected_result[1] == "Artist":
            select_artist(selected_result)

def search_sp(uid):
    # allows the user to search for a song or playlist
    global connection, cur
    connection.row_factory = sqlite3.Row
    print("===================================")
    print("Searching for songs and playlists")
    print("===================================")

    keywords = input("Please enter your search: ")

    get_ps = """
                WITH ps_results(id, type, title, duration, sim_count) as (
                SELECT sid, 'Song' as type, s.title, duration, sim_words(UPPER(title), UPPER(:usearch)) as sim_count
                FROM songs s
                WHERE sim_count > 0
                UNION
                SELECT p.pid, 'Playlist' as type, p.title, sum(s.duration), sim_words(UPPER(p.title), UPPER(:usearch)) as sim_count
                FROM playlists p, songs s, plinclude pi
                WHERE sim_count > 0
                and p.pid = pi.pid
                and pi.sid = s.sid
                GROUP BY p.pid, p.title
                )
                SELECT * 
                FROM ps_results
                ORDER BY sim_count DESC;
                """

    cur.execute(get_ps, {"usearch": keywords})
    ps_results = cur.fetchall()
    ps_pages = format_page(ps_results)
    print(ps_pages)
    display_pages(ps_pages)

    home(uid)


def search_artist(uid):
    # allows the user to search for an artist
    global connection, cur
    print("===================================")
    print("Searching for artists")
    print("===================================")

    keywords = input("Please enter your search: ")

    get_as = """
                WITH as_results(aid, type, name, nationality, song_count, sim_count) as (
                SELECT a.aid, 'Artist' as type, a.name, a.nationality, COUNT(p.sid) as song_count, sim_words(UPPER(a.name), UPPER(:usearch)) as sim_count
                FROM artists a, perform p
                WHERE a.aid = p.aid
                and sim_count > 0
                GROUP BY a.aid, a.name, a.nationality
                UNION
                SELECT a.aid, 'Artist' as type, a.name, a.nationality, COUNT(p.sid) as song_count, sim_words(UPPER(s.title), UPPER(:usearch)) as sim_count
                FROM songs s, perform p, artists a
                WHERE sim_count > 0
                and s.sid = p.sid
                and p.aid = a.aid
                GROUP BY a.aid, a.name, a.nationality
                )
                SELECT * 
                FROM as_results
                ORDER BY sim_count DESC;
            """

    cur.execute(get_as, {"usearch": keywords})
    as_results = cur.fetchall()
    as_pages = format_page(as_results)

    if len(as_pages) == 0:
        home(uid)

    display_pages(as_pages)
    home(uid)

def end_session(uid):
    # allows the user to end their session
    global connection, cur

    current_date = time.strftime("%Y-%m-%d")

    print("===================================")
    print("SESSION ENDED")
    print("===================================")

    update_session = """
                    UPDATE sessions
                    SET end = :curtime
                    WHERE uid = :userid
                    and end IS NULL;
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
        search_sp(uid)
    elif user_choice == "3":
        search_artist(uid)
    elif user_choice == "4":
        end_session(uid)
    elif user_choice == "5":
        login(uid)
    else:
        print("Invalid input.")
        home(uid)

def exits(input):
    if input.lower() == 'exit':
        exit()

def login():
    global connection, cur
    # login screen to retrieve account and detect if account is user, artist, or both

    # welcome screen
    print("\n======================================")
    print("Welcome to UAtify!".center(35))
    print("Canada's top music streaming platform".center(35))
    print("Please login below".center(35))
    print("======================================")
    print("\nEnter 'exit' at any time to logout")

    # getting all user ids
    cur.execute("Select uid from users;")
    connection.commit()
    old_users = cur.fetchall()
    # fetchall() returns items in a tuple, so each item will be
    # equal to (uid,)
    # this loop removes the comma and populates first_users with the ids
    first_users = [user[0] for user in old_users]
    # this loop returns the lowercase version of all ids to help
    # with case insensitivity
    users = [str(id).lower() for id in first_users]

    # getting all artist ids
    cur.execute("Select aid From artists;")
    connection.commit()
    old_artists = cur.fetchall()
    # fetchall() returns items in a tuple, so each item will be
    # equal to (aid,)
    # this loop removes the comma and populates first_artists with the ids
    first_artists = [artist[0] for artist in old_artists]
    # this loop returns the lowercase version of all ids to help
    # with case insensitivity
    artists = [str(name).lower() for name in first_artists]

    # asking user if they want to make an account or login
    answer = input("\nDo you want to make a new account (n) or login (l)? Enter n or l: ")
    # exits() checks if user wants to exit code
    # will be used any time user enters an input
    exits(answer)
    while answer.lower() != "n" and answer.lower() != "l":
        answer = input("Do you want to make a new account (n) or login (l)? Enter n or l: ")
        exits(answer)

    # adding new user
    if answer.lower() == 'n':
        new_uid = input("\nPlease enter a 4 character unique id: ")
        exits(new_uid)
        # while the entered id is not unique or is longer than 4 characters
        while new_uid.lower() in users or len(new_uid) > 4:
            new_uid = input("\nPlease enter a unique id that is not longer than 4 characters: ")
            exits(new_uid)
        name = input("\nPlease enter your name: ")
        exits(name)
        password = input("\nPlease enter a new password: ")
        exits(password)
        # adding user id to users list
        users.append(new_uid.lower())
        # inserting information about new user into users table
        cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})
        connection.commit()
        # returning id and 'user' to help identify if person logging in is a user or artist
        return (new_uid.lower(), 'user')


    # logging in
    if answer.lower() == 'l':
        user_id = input("\nPlease enter your id: ")
        exits(user_id)
        # lower() helps with matching with case insensitivity
        id = user_id.lower()
        # if id is a user id and not an artist id
        if id in users and id not in artists:
            password = input("\nPlease enter your password: ")
            exits(password)
            # get password for person with selected id
            cur.execute("Select pwd from users where uid = :id;", {"id": id})
            connection.commit()
            pwd = cur.fetchone()[0]
            while password != pwd:
                password = input("\nIncorrect password. Please try again: ")
                exits(password)
            return (id, 'user')
        
        # if id is not a user id and an artist id
        elif id in artists and id not in users:
            password = input("\nPlease enter your password: ")
            exits(password)
            cur.execute("Select pwd from artists where aid = :id;", {"id": id})
            connection.commit()
            pwd = cur.fetchone()[0]
            while password != pwd:
                password = input("\nIncorrect password. Please try again: ")
                exits(password)
            return (id, 'artist')
        
        # if id is both an artist id and a user id
        elif id in artists and id in users:
            # ask person if they want to login as an artist or user
            log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
            exits(log_choice)
            while log_choice.lower() not in ['u', 'a']:
                log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
                exits(log_choice)
            # person logs in as a user
            if log_choice.lower() == 'u':
                password = input("\nPlease enter your password: ")
                exits(password)
                cur.execute("Select pwd from users where uid = :id;", {"id": id})
                connection.commit()
                pwd = cur.fetchone()[0]
                while password != pwd:
                    password = input("\nIncorrect password. Please try again: ")
                    exits(password)
                return (id, 'user')
            # person logs in as an artist
            elif log_choice.lower() == 'a':
                password = input("\nPlease enter your password: ")
                exits(password)
                cur.execute("Select pwd from artists where aid = :id;", {"id": id})
                connection.commit()
                pwd = cur.fetchone()[0]
                while password != pwd:
                    password = input("\nIncorrect password. Please try again: ")
                    exits(password)
                return (id, 'artist')
        
        # if id belongs to someone not registered yet
        elif id not in artists and id not in users: 
            print("\nYou have to make a new user account")
            # prompt them to make a new user account
            new_uid = input("\nPlease enter a 4 character unique id: ")
            exits(new_uid)
            while new_uid.lower() in users or len(new_uid) > 4:
                new_uid = input("\nPlease enter a unique id that is not longer than 4 characters: ")
                exits(new_uid)
            name = input("\nPlease enter your name: ")
            exits(name)
            password = input("\nPlease enter a new password: ")
            exits(password)
            users.append(new_uid.lower())
            cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})
            connection.commit()
            return (new_uid.lower(), 'user')
        

def main():
    global connection, cur

    # retrieve database from command line
    db = sys.argv[1]

    # retrieve path to connect to
    path = "./{database}".format(database=db)
    connect(path) 
    connection.create_function("sim_words", 2, similar_words)

    # main program
    uid = login()
    home(uid)

    # close connection and finish program
    connection.commit()
    connection.close()
    return

if __name__ == "__main__":
    main()
