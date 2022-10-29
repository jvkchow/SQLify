from asyncio.windows_events import NULL
from re import S
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

    connection.commit()

    return sno

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
        if result[1] == "Artist":
            print("Type: " + result[1] + ", Name: " + result[2] + ", Nationality: " + str(result[3]).upper() + ", ID: " + str(result[0]))
        else:
            print("Type: " + result[1] + ", Title: " + result[2] + ", Duration: " + str(result[3]) + ", ID: " + str(result[0]))
        counter += 1
    print("===================================")
    return

def listen(song, uid):
    # actions that occur when listening to a song
    print("===================================")
    print("LISTENING TO SONG...")
    print("===================================")

    # check if session is opened and add to listen event (if not opened start a new session)
    check_session = """
                    SELECT *
                    FROM sessions
                    WHERE uid = :userid
                    and end IS NULL;
                    """
    cur.execute(check_session, {"userid": uid})
    session = cur.fetchone()

    if session == None:
        print("You are currently not in a session.")
        print("Start a new session...")
        sno = start_session(uid)
    else:
        sno = session[1]

    # check if have listened to the song before in this session

    check_listen = """
                    SELECT cnt
                    FROM listen
                    WHERE uid = :userid
                    and sno = :sesno
                    and sid = :cur_song
                   """
    cur.execute(check_listen, {"userid": uid, "sesno": sno, "cur_song": song[0]})
    listened = cur.fetchone()

    if listened == None:
        insert_listen = """
                        INSERT INTO listen(uid, sno, sid, cnt)
                        VALUES (:userid, :sesno, :cur_song, 1)
                        """
        cur.execute(insert_listen, {"userid": uid, "sesno": sno, "cur_song": song[0]})
    else:
        update_listen = """
                        UPDATE listen
                        SET cnt = cnt + 1
                        WHERE uid = :userid
                        and sno = :sesno
                        and sid = :cur_song
                        """
        cur.execute(update_listen, {"userid": uid, "sesno": sno, "cur_song": song[0]})

    connection.commit()
    print("Listening complete.")
    return

def song_info(song):
    # actions to display extra song information
    print("===================================")
    print("SONG INFO")
    print("===================================")

    get_artist = """
                    SELECT a.name
                    FROM artists a, perform p
                    WHERE a.aid = p.aid
                    and p.sid = :cur_song;
                 """

    cur.execute(get_artist, {"cur_song": song[0]})
    artists = cur.fetchall()

    print("Song Title: " + song[2])
    print("Song Duration: " + str(song[3]))
    print("Song ID: " + str(song[0]))
    print("Artist(s):")
    for artist in artists:
        print(artist[0])

    get_playlists = """
                    SELECT py.title
                    FROM playlists py, plinclude pi
                    WHERE py.pid = pi.pid
                    and pi.sid = :cur_song;
                    """
    cur.execute(get_playlists, {"cur_song": song[0]})
    playlists = cur.fetchall()

    if len(playlists) > 0:
        print("Playlists this song is in:")
        for playlist in playlists:
            print(playlist[0])
    else:
        print("This song is not in any playlist.")

    return
    
def add_song(pid, sid):
    retrieve_playlist = """
                        SELECT * 
                        FROM plinclude pi
                        WHERE pi.pid = :input_id
                        ORDER BY sorder DESC;
                        """
    cur.execute(retrieve_playlist, {"input_id": pid})
    playlist = cur.fetchall()

    if len(playlist) > 0:
        old_sorder = int(playlist[0][2])
        new_sorder = old_sorder + 1
    else:
        new_sorder = 0

    add_song = """
                INSERT INTO plinclude(pid, sid, sorder)
                VALUES (:id, :song, :order);
                """
    cur.execute(add_song, {"id": pid, "song": sid, "order": new_sorder})

    print("Song successfully added.")
    connection.commit()
    return

def playlist_add(song, uid):
    # actions that occur when adding a song to a playlist
    print("===================================")
    print("ADDING SONG TO PLAYLIST...")
    print("===================================")
    print(""" 
            Enter 'a' if you would like to add this song to an existing playlist
            Enter 'n' if you would like to create a new playlist to add this song to
            """)

    choice = input("Please enter your choice: ")

    if choice == 'a':
        id = input("Please enter the unique playlist id: ")
        add_song(int(id), song[0])

    elif choice == 'n':
        name = input("Please enter the title you want the new playlist to have: ")

        # check if this playlist is the first one added
        cur.execute("SELECT COUNT(*) FROM playlists;")
        py_count = cur.fetchone()
        if py_count[0] == 0:
            pid = 1
        else:
            # get unique sno by adding 1 to the last sno added
            cur.execute("SELECT pid FROM playlists;")
            pids = cur.fetchall()
            largest_pid = pids[len(pids)-1][0]
            pid = largest_pid + 1

        new_playlist = """
                        INSERT INTO playlists(pid, title, uid)
                        VALUES (:pyid, :title, :userid);
                       """

        cur.execute(new_playlist, {"pyid": pid, "title": name, "userid": uid})
        connection.commit()
        add_song(pid, song[0])

    else:
        print("Invalid selection.")

    return

def select_song(song, uid):
    # actions that occur when you select a song
    print("===================================")
    print("SELECTED SONG: " + song[2])
    print("===================================")
    print("""
            Please select an action:
            Enter 1 to listen to the song
            Enter 2 to see more information about the song
            Enter 3 to add this song to a playlist
        """)
    print("===================================")

    action = input("Please enter your choice: ")

    if action == "1":
        listen(song, uid)
    elif action == "2":
        song_info(song)
    elif action == "3":
        playlist_add(song, uid)
    else:
        print("Invalid input.")
    return


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
        return user_choice
    else:
        choice = user_choice.split(".")
        selected_page = pages[int(choice[0])]
        selected_result = selected_page[int(choice[1])]

        return selected_result

def list_songs(songs):
    if len(songs) == 0:
        print("No songs to display.")
        return None

    song_counter = 0
    for song in songs:
        print("Result Number: " + str(song_counter) + ", Title: " + song[2] + ", Duration: " + str(song[3]) + ", ID: " + str(song[0]))
        song_counter += 1

    user_choice = input("If you would like to select a result, enter the result number: [Result Number]. If not, enter 'n': ")

    if user_choice == 'n':
        return user_choice
    elif user_choice.isnumeric() and int(user_choice) >= 0 and int(user_choice) < len(songs):
        selected_result = songs[int(user_choice)]
        return selected_result
    else:
        print("Invalid search.")
        return None

def select_artist(artist):
    # actions that occur when you select a playlist
    print("===================================")
    print("SELECTED ARTIST: " + artist[2])
    print("===================================")

    print("Artist ID: " + str(artist[0]))
    print("Artist Name: " + artist[2])

    get_songs = """
                SELECT s.sid, "Song" as type, s.title, s.duration, NULL as sim_count
                FROM songs s, perform p
                WHERE p.aid = :cur_artist
                and p.sid = s.sid
                """
    cur.execute(get_songs, {"cur_artist": artist[0]})
    artist_songs = cur.fetchall()

    selection = list_songs(artist_songs)
    return selection

def select_playlist(playlist):
    # actions that occur when you select a playlist
    print("===================================")
    print("SELECTED PLAYLIST: " + playlist[2])
    print("===================================")

    print("Playlist ID: " + str(playlist[0]))
    print("Playlist Title: " + playlist[2])

    get_songs = """
                SELECT s.sid, "Song" as type, s.title, s.duration, NULL as sim_count
                FROM songs s, plinclude pi
                WHERE pi.pid = :cur_py
                and pi.sid = s.sid
                ORDER BY pi.sorder ASC
                """
    cur.execute(get_songs, {"cur_py": playlist[0]})

    py_songs = cur.fetchall()

    selection = list_songs(py_songs)
    return selection

def process_selection(selection, uid):
    if selection[1] == "Song":
        select_song(selection, uid)
    else:
        if selection[1] == "Playlist":
            choice = select_playlist(selection)
        else: # selection[1] == "Artist":
            choice = select_artist(selection)
        if choice != 'n' and choice != None:
            select_song(choice, uid)
        
    return

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

    if len(ps_pages) == 0:
        return 'n'

    selection = display_pages(ps_pages)

    return selection

def search_artist():
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
        return 'n'

    selection = display_pages(as_pages)

    return selection

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
    return

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
        return True
    elif user_choice == "2":
        selection = search_sp()
        if selection != 'n' and selection != None:
            process_selection(selection, uid)
        return True
    elif user_choice == "3":
        selection = search_artist()
        if selection != 'n' and selection != None:
            process_selection(selection, uid)
        return True
    elif user_choice == "4":
        end_session(uid)
        return False
    elif user_choice == "5":
        login()
        return True
    else:
        print("Invalid input.")
        return True

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
    connection.create_function("sim_words", 2, similar_words)

    # main program
    #uid = login()

    continue_session = True
    while continue_session:
        continue_session = home("u03")

    # close connection and finish program
    connection.commit()
    connection.close()
    return

if __name__ == "__main__":
    main()
