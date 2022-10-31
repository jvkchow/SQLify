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

def exit_program():
    # exits the program for an artist
    print("Exiting the program...")
    sys.exit()

def check_open_session(uid):
    # check if there are any open sessions and ends them if there are
    cur.execute("SELECT * FROM sessions WHERE uid=:userid and end IS NULL", {"userid": uid})
    open_session = cur.fetchone()
    if open_session != None:
        end_session(uid)
    return

def user_exit(uid):
    # exits the program for a user
    check_open_session(uid)
    exit_program()

def user_logout(uid):
    # logs the user out
    check_open_session(uid)
    print("Logging out...")
    return

def start_session(uid):
    # starts a session for the user

    global connection, cur

    current_date = time.strftime("%Y-%m-%d")

    # check if user is not in another session
    cur.execute("SELECT * FROM sessions WHERE uid=:userid and end IS NULL", {"userid": uid})
    possible_ses = cur.fetchone()
    if possible_ses != None:
        print("You are already in a session.")
        return

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

    # adds a new session
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
    # gets the number of similar words between dbword and usearch and returns the result

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
    # prints a result page

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

    # checks if session is opened
    check_session = """
                    SELECT *
                    FROM sessions
                    WHERE uid = :userid
                    and end IS NULL;
                    """
    cur.execute(check_session, {"userid": uid})
    session = cur.fetchone()

    # if a session is not opened, create a new one
    if session == None:
        print("You are currently not in a session.")
        print("Start a new session...")
        sno = start_session(uid)
    else:
        sno = session[1]

    # check if user has listened to the song before in this session
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
        # if they have not listened to the song yet, insert a new listen entry in the listen table
        insert_listen = """
                        INSERT INTO listen(uid, sno, sid, cnt)
                        VALUES (:userid, :sesno, :cur_song, 1)
                        """
        cur.execute(insert_listen, {"userid": uid, "sesno": sno, "cur_song": song[0]})
    else:
        # if they have listened to the song already, update the old listen count value
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
    # displays a song's title, duration, ID, artists that performed it, and playlists it's in

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

    # gets the playlists the song is in
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
    # adds a song to a playlist

    # get the given playlist to find how many songs have already been added to it
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

    # add the song into the playlist
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
            Enter 'e' if you would like to exit the program
            """)

    choice = input("Please enter your choice: ")

    if choice == 'e':
        user_exit(uid)

    elif choice == 'a':
        id = input("Please enter the unique playlist id: ")

        # check to see if the playlist exists
        cur.execute("SELECT * FROM playlists WHERE pid = :input_id", {"input_id": id})
        possible_py = cur.fetchone()
        if possible_py == None:
            print("This playlist does not exist. Adding to playlist process terminated.")
        else:
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
            Enter 4 to exit the program
        """)
    print("===================================")

    action = input("Please enter your choice: ")

    if action == "1":
        listen(song, uid)
    elif action == "2":
        song_info(song)
    elif action == "3":
        playlist_add(song, uid)
    elif action == "4":
        user_exit(uid)
    else:
        print("Invalid input.")
    return


def format_page(results):
    # puts results into a page formatted list and returns the list
    
    pages = []
    counter = 0

    # check if there are results matching the search
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

def display_pages(pages, uid):
    # provides the user options on whether to go to the next page and to select a result
    # returns the user's selection

    exit_choice = input("If you would like to exit the program, enter 'e'. Otherwise, enter any input: ")
    if exit_choice == 'e':
        user_exit(uid)
    print("Displaying pages...")

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

    # retrieves user's selection
    if user_choice == 'n':
        return user_choice
    elif "." not in user_choice:
        print("Invalid format. Selection process terminated.")
        return None
    else:
        choice = user_choice.split(".")

        if (not choice[0].isnumeric()) or (not choice[1].isnumeric()):
            print("Invalid format. Selection process terminated.")
            return None

        selected_page = pages[int(choice[0])]
        selected_result = selected_page[int(choice[1])]

        return selected_result

def list_songs(songs):
    # lists songs given by the songs parameter in a readable format

    # checks if there are songs in the playlist
    if len(songs) == 0:
        print("No songs to display.")
        return None

    song_counter = 0
    for song in songs:
        print("Result Number: " + str(song_counter) + ", Title: " + song[2] + ", Duration: " + str(song[3]) + ", ID: " + str(song[0]))
        song_counter += 1

    user_choice = input("If you would like to select a result, enter the result number: [Result Number]. If not, enter 'n': ")

    # retrieve user's selection
    if user_choice == 'n':
        return user_choice
    elif user_choice.isdigit() and int(user_choice) >= 0 and int(user_choice) < len(songs):
        selected_result = songs[int(user_choice)]
        return selected_result
    else:
        print("Invalid search.")
        return None

def select_artist(artist):
    # displays an artist's ID, name, and songs

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
    # displays a playlist's ID, title, and songs that are in it
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
    # performs an action depending on whether a user has selected a song, playlist, or an artist

    if selection[1] == "Song":
        select_song(selection, uid)
    else:
        if selection[1] == "Playlist":
            choice = select_playlist(selection)
        else: # selection == "Artist"
            choice = select_artist(selection)
        if choice != 'n' and choice != None:
            # if the user wants to select a song in a playlist or a song that an artist has performed
            select_song(choice, uid)
        
    return

def search_sp(uid):
    # allows the user to search for a song or playlist
    global connection, cur
    connection.row_factory = sqlite3.Row
    print("===================================")
    print("Searching for songs and playlists")
    print("===================================")

    keywords = input("Please enter your search: ")

    # gets song and playlist information if some of the song/playlist's title matches some of the user's search
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

    # check if there are results
    if len(ps_pages) == 0:
        print("No song or playlist matches your search.")
        return None

    selection = display_pages(ps_pages, uid)

    return selection

def search_artist(uid):
    # allows the user to search for an artist
    global connection, cur
    print("===================================")
    print("Searching for artists")
    print("===================================")

    keywords = input("Please enter your search: ")

    # gets artist information if some of their name or the song's title matches some of the user's search

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

    # check if there are results
    if len(as_pages) == 0:
        print("No artist matches your search.")
        return None

    selection = display_pages(as_pages, uid)

    return selection

def end_session(uid):
    # ends a user's session

    global connection, cur

    current_date = time.strftime("%Y-%m-%d")

    # check if there is an open session
    cur.execute("SELECT * FROM sessions WHERE uid=:userid and end IS NULL", {"userid": uid})
    open_session = cur.fetchone()
    if open_session == None:
        print("You are not in any session.")
        return

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

def user_home(uid):
    # home screen for the user to select an action
    print("===================================")
    print("Welcome to the user home screen!")
    print("""
            Enter 1 to start a session
            Enter 2 to search for songs and playlists
            Enter 3 to search for artists
            Enter 4 to end the session
            Enter 5 to logout
            Enter 6 to exit the program
        """)
    print("===================================")
    user_choice = input("Please enter your choice: ")

    if user_choice == "1":
        start_session(uid)
        return True
    elif user_choice == "2":
        selection = search_sp(uid)
        if selection != 'n' and selection != None:
            process_selection(selection, uid)
        return True
    elif user_choice == "3":
        selection = search_artist(uid)
        if selection != 'n' and selection != None:
            process_selection(selection, uid)
        return True
    elif user_choice == "4":
        end_session(uid)
        return False
    elif user_choice == "5":
        user_logout(uid)
        return True
    elif user_choice == "6":
        user_exit(uid)
    else:
        print("Invalid input.")
        return True

def upload_song(aid):
    # uploads a song for an artist

    print("===================================")
    print("Uploading song...")
    print("===================================")

    title = input("Please enter the title of your song: ")
    duration = input("Please enter your song duration: ")

    # checks if the user entered the proper data for duration
    if not duration.isdigit():
        print("Your song duration must be a positive integer.\nUploading process terminated.")
        return

    artist_count = input("Please enter a number to indicate how many artists worked on this song in total: ")

    # checks if the user entered the proper data for artist count
    if not artist_count.isdigit():
        print("The amount of artists that worked on this song must be a positive integer.\nUploading process terminated.")
        return

    artists = []
    artists.append(aid)

    # if there is more than one artist, get the artist id's of the other ones
    if int(artist_count) > 1:
        count = 1
        while count < int(artist_count):
            additional_artist = input("Please enter the artist id of an additional artist: ")

            # check if artist id exists
            cur.execute("SELECT * FROM artists WHERE aid = :input_id", {"input_id": additional_artist})
            possible_artist = cur.fetchone()
            if possible_artist == None:
                print("This artist is not registered in the system.")
            elif additional_artist not in artists:
                artists.append(additional_artist)
                count += 1
            else:
                print("You already said this artist.")

    # check to see if the song has not already been uploaded
    check_song = """
                    WITH matching_song(sid) as (
                    SELECT sid
                    FROM songs
                    WHERE title = :chosen_title
                    and duration = :chosen_duration
                    )
                    SELECT *
                    FROM artists a, matching_song m, perform p
                    WHERE a.aid = :cur_artist
                    and p.sid = m.sid
                    and p.aid = :cur_artist;
                 """

    cur.execute(check_song, {"cur_artist": aid, "chosen_title": title, "chosen_duration": int(duration)})
    songs = cur.fetchone()

    # adds the song to the database
    if songs == None:

        cur.execute("SELECT sid FROM songs ORDER BY sid DESC;")
        sids = cur.fetchall()
        old_sid = sids[0][0]
        new_sid = old_sid + 1

        add_song = """
                    INSERT INTO songs(sid, title, duration)
                    VALUES (:song_id, :song_title, :song_duration);
                   """
        cur.execute(add_song, {"song_id": new_sid, "song_title": title, "song_duration": duration})

        for artist in artists:
            add_artist_song = """
                                INSERT INTO perform(aid, sid)
                                VALUES (:cur_artist, :new_sid);
                            """
            cur.execute(add_artist_song, {"cur_artist": artist, "new_sid": new_sid})
        connection.commit()
        print("Song successfully uploaded.")
    else:
        print("You have already uploaded this song.")

    return

def find_for_artist(aid):
    # find sthe top 3 fans and playlists of an artist
    print("===================================")
    print("TOP 3 FANS:")
    print("===================================")

    # finds the top 3 fans
    find_fans = """
                    SELECT u.uid, u.name, sum(l.cnt*s.duration) as listens
                    FROM users u, listen l, perform p, songs s
                    WHERE u.uid = l.uid
                    and l.sid = p.sid
                    and l.sid = s.sid
                    and p.aid = :cur_artist
                    GROUP BY u.uid
                    ORDER BY listens DESC
                    LIMIT 3;
                """
    cur.execute(find_fans, {"cur_artist": aid})
    fans = cur.fetchall()

    if len(fans) == 0:
        print("You have no fans.")
    else:
        for fan in fans:
            print("User ID: " + fan[0], ", Name: " + fan[1])

    print("===================================")
    print("TOP 3 PLAYLISTS:")
    print("===================================")

    # finds the top 3 playlists
    find_playlists = """
                        SELECT py.pid, py.title, sum(s.sid) as artist_songs
                        FROM playlists py, songs s, perform p, plinclude pi
                        WHERE py.pid = pi.pid
                        and s.sid = pi.sid
                        and s.sid = p.sid
                        and p.aid = :cur_artist
                        GROUP BY py.pid
                        ORDER BY artist_songs DESC
                        LIMIT 3;
                     """
    cur.execute(find_playlists, {"cur_artist": aid})
    playlists = cur.fetchall()

    if len(playlists) == 0:
        print("Your songs are not in any playlists.")
    else:
        for playlist in playlists:
            print("Playlist ID: " + str(playlist[0]) + ", Playlist Title: " + playlist[1])

    return

def artist_home(aid):
    # artist home screen the artist to select an action
    print("===================================")
    print("Welcome to the artist home screen!")
    print("""
            Enter 1 to add a song
            Enter 2 to find top fans and playlists
            Enter 3 to log out
            Enter 4 to exit the program
          """)
    print("===================================")
    artist_choice = input("Please enter your choice: ")

    if artist_choice == "1":
        upload_song(aid)
        return True
    elif artist_choice == "2":
        find_for_artist(aid)
        return True
    elif artist_choice == "3":
        print("Logging out...")
        return False
    elif artist_choice == "4":
        exit_program()
    else:
        print("Invalid input.")
        return True


def login():
    global connection, cur
    # login screen to retrieve account and detect if account is user, artist, or both
    print("\n======================================")
    print("Welcome to UAtify!".center(35))
    print("Canada's top music streaming platform".center(35))
    print("Please login below".center(35))
    print("======================================")
    print("\nEnter 'exit' at any time to logout")

    cur.execute("Select uid from users;")
    connection.commit()
    old_users = cur.fetchall()
    first_users = [user[0] for user in old_users]
    users = [str(id).lower() for id in first_users]

    cur.execute("Select aid From artists;")
    connection.commit()
    old_artists = cur.fetchall()
    first_artists = [artist[0] for artist in old_artists]
    artists = [str(name).lower() for name in first_artists]

    answer = input("\nDo you want to make a new account (n) or login (l)? Enter n or l: ")
    if answer == 'exit':
        exit()
    while answer.lower() != "n" and answer.lower() != "l":
        answer = input("Do you want to make a new account (n) or login (l)? Enter n or l: ")
        if answer == 'exit':
            exit()

    # adding new user
    if answer.lower() == 'n':
        new_uid = input("\nPlease enter a 4 character unique id: ")
        if new_uid == 'exit':
            exit()
        while new_uid.lower() in users or len(new_uid) > 4:
            new_uid = input("\nPlease enter a unique id that is not longer than 4 characters: ")
            if new_uid == 'exit':
                exit()
        name = input("\nPlease enter your name: ")
        password = input("\nPlease enter a new password: ")
        users.append(new_uid.lower())
        cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})
        connection.commit()
        return (new_uid.lower(), 'user')


    # logging in
    if answer.lower() == 'l':
        user_id = input("\nPlease enter your id: ")
        if user_id == 'exit':
            exit()
        id = user_id.lower()

        if id in users and id not in artists:
            password = input("\nPlease enter your password: ")
            cur.execute("Select pwd from users where uid = :id;", {"id": id})
            connection.commit()
            pwd = cur.fetchone()[0]
            while password != pwd:
                password = input("\nIncorrect password. Please try again: ")
            return (id, 'user')
            
        elif id in artists and id not in users:
            password = input("\nPlease enter your password: ")
            cur.execute("Select pwd from artists where aid = :id;", {"id": id})
            connection.commit()
            pwd = cur.fetchone()[0]
            while password != pwd:
                password = input("\nIncorrect password. Please try again: ")
            return (id, 'artist')
            
        elif id in artists and id in users:
            log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
            while log_choice.lower() not in ['u', 'a']:
                log_choice = input("\nDo you want to login as a user or an artist? Please enter u or a: ")
            if log_choice.lower() == 'u':
                password = input("\nPlease enter your password: ")
                cur.execute("Select pwd from users where uid = :id;", {"id": id})
                connection.commit()
                pwd = cur.fetchone()[0]
                while password != pwd:
                    password = input("\nIncorrect password. Please try again: ")
                return (id, 'user')
            elif log_choice.lower() == 'a':
                password = input("\nPlease enter your password: ")
                cur.execute("Select pwd from artists where aid = :id;", {"id": id})
                connection.commit()
                pwd = cur.fetchone()[0]
                while password != pwd:
                    password = input("\nIncorrect password. Please try again: ")
                return (id, 'artist')
                    
        elif id not in artists and id not in users: 
            print("\nYou have to make a new user account")
            new_uid = input("\nPlease enter a 4 character unique id: ")
            if new_uid == 'exit':
                exit()
            while new_uid.lower() in users or len(new_uid) > 4:
                new_uid = input("\nPlease enter a unique id that is not longer than 4 characters: ")
                if new_uid == 'exit':
                    exit()
            name = input("\nPlease enter your name: ")
            password = input("\nPlease enter a new password: ")
            users.append(new_uid.lower())
            cur.execute("INSERT INTO users VALUES (:uid, :name, :pwd)", {"uid": new_uid, "name": name, "pwd": password})
            connection.commit()
            return (new_uid.lower(), 'user')
        
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
    login_info = login()

    if login_info[1] == "user":
        continue_user_session = True
        while continue_user_session:
            continue_user_session = user_home(login_info[0])
    else:
        continue_artist_session = True
        while continue_artist_session:
            continue_artist_session = artist_home(login_info[0])

    # close connection and finish program
    connection.commit()
    connection.close()
    return

if __name__ == "__main__":
    main()
