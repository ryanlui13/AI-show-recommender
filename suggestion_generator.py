import heapq
import gzip
import sqlite3
import pandas as pd 
import os

class User:
    #constructor for user
    def __init__(self, user, age, previous_love_shows=None, previous_like_shows=None):
        self.user = user
        self.age = age 
        #prev ranks 
        self.previous_love_shows = set(previous_love_shows) if previous_love_shows else set()
        self.previous_like_shows = set(previous_like_shows) if previous_like_shows else set()
        
        #genres prefered
        self.loved_genres = set()
        self.liked_genres = set()
        self.hated_genres = set()

        self.preferences = {}
    
    #add info
    def create_profile(self, loved_genres, liked_genres, hated_genres, previous_love_shows, previous_like_shows, preference_dict):
        #love
        if isinstance(loved_genres, (list, set)):
            self.loved_genres.update(loved_genres)
        else:
            self.loved_genres.add(loved_genres) 
        
        #like / ok
        if isinstance(liked_genres, (list, set)):
            self.liked_genres.update(liked_genres)
        else:
            self.liked_genres.add(liked_genres) 
    
        #hate 
        if isinstance(hated_genres, (list, set)):
            self.hated_genres.update(hated_genres)
        else:
            self.hated_genres.add(hated_genres) 
    
        #show data
        if isinstance(previous_love_shows, (set, list)):
            self.previous_love_shows.update(previous_love_shows)
        else:
            self.previous_love_shows.add(previous_love_shows)
        
        if isinstance(previous_like_shows, (set, list)):
            self.previous_like_shows.update(previous_like_shows)
        else:
            self.previous_like_shows.add(previous_like_shows)

        self.preferences.update(preference_dict)

    def display_profile(self):
        print(f" User Profile: {self.user} (Age: {self.age}) ")
        print(f"Loved genres: {self.loved_genres}")
        print(f"Liked genres: {self.liked_genres}")

        print(f"Hated genres: {self.hated_genres}")
        print(f"Shows: {self.previous_shows}")
        print(f"extra preferences: {self.preferences}\n")
    
    #add genres
    def add_genres(self, genre_list, genre_to_add):
        print("Updating genres now...")

        if genre_list == "like":
            if isinstance(genre_to_add, (list, set)):
                self.liked_genres.update(genre_to_add)
            else:
                self.liked_genres.add(genre_to_add) 
        elif genre_list == "love":
            if isinstance(genre_to_add, (list, set)):
                self.loved_genres.update(genre_to_add)
            else:
                self.loved_genres.add(genre_to_add)
        elif genre_list == "hate":
            if isinstance(genre_to_add, (list, set)):
                self.hated_genres.update(genre_to_add)
            else:
                self.hated_genres.add(genre_to_add)
        else:
            print("Enter 'like', 'love' or 'hate'...")

    def remove_genres(self, genre_list, genres_to_remove):
        print("Update genres from profile")
        
        if genre_list == "loved_genres":
            #love 
            if isinstance(genres_to_remove, (list, set)):
                for genre in genres_to_remove:
                    clean_genre = genre.capitalize().strip()
                    self.loved_genres.discard(clean_genre)
                    self.hated_genres.add(clean_genre)
                    print(f"removed: {clean_genre}")
            else:
                clean_genre = genres_to_remove.capitalize().strip()
                self.loved_genres.discard(clean_genre)
                self.hated_genres.add(clean_genre)
                print(f" removed: {clean_genre}")
        elif genre_list == "liked_genres":
            #like 
            if isinstance(genres_to_remove, (list, set)):
                for genre in genres_to_remove:
                    clean_genre = genre.capitalize().strip()
                    self.liked_genres.discard(clean_genre)
                    self.hated_genres.add(clean_genre)
                    print(f"removed: {clean_genre}")
            else:
                clean_genre = genres_to_remove.capitalize().strip()
                self.liked_genres.discard(clean_genre)
                self.hated_genres.add(clean_genre)
                print(f" removed: {clean_genre}")
        elif genre_list == "hated_genres":
            if isinstance(genres_to_remove, (list, set)):
                for genre in genres_to_remove:
                    clean_genre = genre.capitalize().strip()
                    self.hated_genres.discard(clean_genre)
                    print(f"removed: {clean_genre}")
            else:
                clean_genre = genres_to_remove.capitalize().strip()
                self.hated_genres.discard(clean_genre)
                print(f" removed: {clean_genre}")
        else:
            print("Enter either 'loved_genres' or 'liked_genres' or 'hated_genres' to remove genre data...")

    #add shows
    def add_shows(self, show_list, shows_to_add):
        print("Updating shows...")

        if show_list == "love list":
            #love list
            if isinstance(shows_to_add, (list, set)):
                self.previous_love_shows.update(shows_to_add)
            else:
                self.previous_love_shows.add(shows_to_add)                
        elif show_list == "like list":
            if isinstance(shows_to_add, (list, set)):
                self.previous_like_shows.update(shows_to_add)
            else:
                self.previous_like_shows.add(shows_to_add)
        else:
            print("Enter 'like list' or 'love list' instead for the wizard to work...")

class Shows:
    def __init__(self, title, genres, cast, rating=0.0, votes=0):
        self.title = title 
        self.genres = genres 
        self.cast = cast 
        self.rating = rating 
        self.votes = votes 

    #add the genres for each show 
    def add_genres(self, new_genres):
        if isinstance(new_genres, (list, set)):
            self.genres.update(new_genres)
        else:
            self.genres.add(new_genres)
    
    #add the cast for each show 
    def add_fav_cast(self, add_cast):
        if isinstance(add_cast, (list, set)):
            self.cast.update(add_cast)
        else:
            self.cast.add(add_cast) 
    
#find shows w/ similar cast
def find_shows_with_cast(previous_love_shows, previous_like_shows, all_shows_database, top_count=10):
    actors_count = {}    #actor, frequency

    #look through the shows
    for show in previous_love_shows:
        for actor in show.cast:    #get actor count for each movie
            #keep track of actors.
            if actor in actors_count:
                actors_count[actor] += 1 
            else:
                actors_count[actor] = 1
    
    for show in previous_like_shows:
        for actor in show.cast:    #get actor count for each movie
            #keep track of actors.
            if actor in actors_count:
                actors_count[actor] += 1 
            else:
                actors_count[actor] = 1

    #build the heap based on 
    fav_cast_shows = []
    for show in all_shows_database:
        if show in previous_love_shows or show in previous_like_shows:
            continue 

        show_cast_score = 0
        for actor in show.cast:
            if actor in actors_count:
                show_cast_score += actors_count[actor]
            
        if show_cast_score > 0:
            heapq.heappush(fav_cast_shows, (-show_cast_score, -show.rating, show.title, show.genres, show.cast))

    show_by_actor = []
    #pop the heap 
    while fav_cast_shows and len(show_by_actor) < top_count:
        score, rating, title, genres, cast = heapq.heappop(fav_cast_shows)
        show_by_actor.append((title, genres, cast, rating))
    
    return show_by_actor

#show recommender
def generate_suggestions(loved_genres, liked_genres, hated_genres, all_shows_database, previous_love_shows, previous_like_shows, top_count = 10):
    #use max-heap to keep track of shows + similar genres
    show_heap = []
    
    if previous_love_shows != None:
        history_genres = set()
        for show in previous_love_shows:
            history_genres.update(show.genres)
    
    if previous_like_shows != None:
        history_genres = set()
        for show in previous_like_shows:
            history_genres.update(show.genres)
    
    loved_genres = loved_genres.union(history_genres)
    liked_genres = set(liked_genres)
    hated_genres = set(hated_genres)

    #search for shows w/ similar genres
    for show in all_shows_database:
        if previous_love_shows and show in previous_like_shows:
            continue
        
        #skip hated genres 
        if show.genres.intersection(hated_genres):
            continue 

        matching_love__genres = loved_genres.intersection(show.genres)
        matching_like_genres = liked_genres.intersection(show.genres)
        matching_actors = show.cast

        #love genre worth 2 times more 
        score = (len(matching_love__genres)*2) + (len(matching_like_genres))

        if score > 0:
            heapq.heappush(show_heap, (-score, -show.rating, show.title, show.genres, show.cast)) #push (score, show) onto heap 
    
    suggestions = []
    while show_heap and len(suggestions) < top_count:
        score, rating, title, genres, cast = heapq.heappop(show_heap)
        suggestions.append((title, genres, cast, rating))
    
    #get the list of shows (ranked best to worst)
    return suggestions 

#search for genres in prefered shows. 
def search_genres(user_profile, all_shows_database):
    #search suggestions list 
    show_suggestions = generate_suggestions(user_profile.loved_genres, user_profile.liked_genres, user_profile.hated_genres, all_shows_database, previous_shows=None, top_count=10)
    
    suggestion_titles = {title for tile, genres, cast, rating in show_suggestions}
    added_genres = set() 

    #match titles back to show object ()
    for show in all_shows_database:
        if show.title in suggestion_titles:
            added_genres.update(show.genres)
    
    added_genres.difference_update(user_profile.hated_genres)
    
    #update the profile for genres
    user_profile.liked_genres.update(added_genres)

#search for shows w/ prefered actors.
def get_actors_from_show(user_profile, all_shows_database):
    show_suggestions = generate_suggestions(user_profile.loved_genres, user_profile.liked_genres, user_profile.hated_genres, all_shows_database, previous_shows=None, top_count=10)
    
    suggestion_titles = {title for title, genres, cast, rating in show_suggestions}

    fav_cast = set()
    for show in all_shows_database:
        if show.title in suggestion_titles:
            fav_cast.update(show.cast)
    
    return fav_cast 

#get highest ranking shows 
def get_highest_ranked(all_shows_database, top_count = 10):
    highest_ranked = []
    for show in all_shows_database:
        if show.votes >= 5000:
            #get the current ranking 
            heapq.heappush(highest_ranked, (-show.rating, show.title)) 
    
    highest_show_results = []
    while highest_ranked and len(highest_ranked) < top_count:
        rank, title = heapq.heappop(highest_ranked)
        highest_show_results.append(title)
    
    return highest_show_results

def build_favorite_show_genres_table(conn, all_shows_database, genre_list):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorite_genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primaryTitle TEXT,
            genres TEXT,
            averageRating REAL,
            numVotes INTEGER,
            cast TEXT        
        ); 
    """)

    print("⏳ Filtering and caching matching shows into SQLite database...")

    for show in all_shows_database:
        for genre in genre_list:
            if genre in show.genres: # Check for overlap
                cast_string = ", ".join(show.cast)
                genre_string = ", ".join(show.genres) # Convert set to text string

                cursor.execute("""
                    INSERT INTO favorite_genres
                    (primaryTitle, genres, averageRating, numVotes, cast)
                    VALUES (?, ?, ?, ?, ?);
                """, (show.title, genre_string, show.rating, show.votes, cast_string))
                
                break 

    conn.commit()
    print("🎉 Relational favorite_genres table built successfully!")

def get_ranked_suggestions_from_db(conn):
    #get carches shows from database. sort based on genre match score
    query = """
        SELECT primaryTitle, genres, averageRating, numVotes, "cast",
        (length(genres) - length(replace(genres, ',', '')) + 1) AS match_score
        FROM favorite_genres 
        ORDER BY match_score DESC, averageRating DESC;
    """

    #read into clean dataframe 
    df_ranked = pd.read_sql_query(query, conn)
    return df_ranked 

def get_user_genres():
    chosen_genres = []
    while True:
        new_genres = input("Enter a genre. To stop entering genres type done: ").strip()
        if new_genres.lower() == 'done':
            break 
        else:
            clean_genre = new_genres.capitalize()
            if clean_genre:
                chosen_genres.append(clean_genre)
                print(f"Added {clean_genre}")
            else:
                print("You added this genre already")
    
    return chosen_genres

def remove_user_genres(user_profile, genre_list):
    removed_genres = []
    while True:
        genre_to_delete = input("Enter a genre. to stop type 'done': ").strip()
        if genre_to_delete.lower() == "done":
            break 
        clean_genre = genre_to_delete.capitalize()
        if genre_list == "like":
            if clean_genre in user_profile.liked_genres:
                user_profile.remove_genres("liked_genre", clean_genre)
                removed_genres.append(clean_genre)
                print(f" Rremoved: {clean_genre}")
            else:
                print(f"{clean_genre} isn't in your liked genres list!!")
        elif genre_list == "love":
            if clean_genre in user_profile.loved_genres:
                user_profile.remove_genres("loved_genres", clean_genre)
                removed_genres.append(clean_genre)
                print(f" Rremoved: {clean_genre}")
            else:
                print(f"{clean_genre} isn't in your loved genres list!!")
        elif genre_list == "hate":
            if clean_genre in user_profile.hated_genres:
                user_profile.remove_genres("hated_genre", clean_genre)
                removed_genres.append(clean_genre)
                print(f" Rremoved: {clean_genre}")
            else:
                print(f"{clean_genre} isn't in your hated genres list!!")
        else:
            print("Enter 'like', 'love' or 'hate' to access your list...")

    return removed_genres 

def update_favorite_show_genres_table(conn, userprofile, genres_to_remove):
    #look through the database
    cursor = conn.cursor()

    #convert into a list
    if isinstance(genres_to_remove, str):
        genres_to_remove = [genres_to_remove]
    
    for genre in genres_to_remove:
        clean_genre = genre.capitalize().strip()

        #search for the genre in the sql table
        cursor.execute("""            
            DELETE FROM favorite_genres
            WHERE genres LIKE '%' || ? || '%';
        """, (clean_genre,))
        
        #update the liked genres list
        userprofile.liked_genres.discard(genre)

    conn.commit() 

if __name__ == "__main__":
    print("⚡ Starting Recommendation Engine...")
    import random 

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'data', 'recommender.db')
    conn = sqlite3.connect(db_path)
    
    print("⏳ Running SQL INNER JOIN to zip movie metadata and ratings together...")
    query = """
        SELECT m.primaryTitle, m.genres, r.averageRating, r.numVotes, GROUP_CONCAT(p.nconst, ",") AS real_cast
        FROM movies m
        INNER JOIN ratings r ON m.tconst = r.tconst
        LEFT JOIN principals p on m.tconst = p.tconst AND (p.category = 'actor' OR p.category = 'actress')
        WHERE r.numVotes >= 5000
        GROUP BY m.tconst;
    """
    
    df_master = pd.read_sql_query(query, conn)
    
    # 🏎️ CRITICAL FIX: Populate your objects FIRST before doing any application work!
    print("🧩 Instantiating Shows objects into system memory database...")
    all_shows_database = []
    
    for row in df_master.itertuples():
        genre_set = set(row.genres.split(',')) if (row.genres and row.genres != 'Unknown' and row.genres != '\\N') else set()

        if isinstance(row.real_cast, str) and row.real_cast != '\\N':
            actual_cast_set = set(row.real_cast.split(','))
        else:
            actual_cast_set = set()

        new_show = Shows(
            title = row.primaryTitle,
            genres = genre_set,
            cast = actual_cast_set,  
            rating = float(row.averageRating),
            votes = int(row.numVotes)
        )
        all_shows_database.append(new_show)

    # 2. Interactively set up User profile
    print("\n👋 Let's expand your profile details!")
    user1 = User(user="ryan_coded", age=21)

    #add love genres
    new_loved_genres = get_user_genres()
    user1.add_genres("love", new_loved_genres)

    #add like genres 
    new_liked_genres = get_user_genres()
    user1.add_genres("like", new_liked_genres)

    #add hate genres
    new_hated_genres = get_user_genres()
    user1.add_genres("hate", new_hated_genres)

    #love shows
    love_show_to_add = input("Enter a show you loved. Type 'done' if you are done adding previous shows")
    while love_show_to_add.lower() != "done":
        matching_show = next((s for s in all_shows_database if s.title.lower() == love_show_to_add.lower()), None)
        if matching_show:
            user1.add_shows("love list",matching_show)
            print(f"Added {matching_show.title} to previous_shows")
        else:
            print("Show not found. try again")

    #like shows 
    like_show_to_add = input("Enter a show you liked. Type 'done' if you are done adding previous shows")
    while like_show_to_add.lower() != "done":
        matching_show = next((s for s in all_shows_database if s.title.lower() == like_show_to_add.lower()), None)
        if matching_show:
            user1.add_shows("like list", matching_show)
            print(f"Added {matching_show.title} to previous_shows")
        else:
            print("Show not found. try again")

    print(f"\n✨ Current profile summary for {user1.user}:")
    print(f" -> Loved Genres: {user1.loved_genres}")
    print(f" -> Loved Genres: {user1.liked_genres}")


    # 3. Handle removals interactively and sync to SQLite
    deleted_genres = remove_user_genres(user1, user1.hated_genres)
    if deleted_genres:
        update_favorite_show_genres_table(conn, user1, deleted_genres)

    # 4. Cache remaining favorite genres to the table
    build_favorite_show_genres_table(conn, all_shows_database, user1.loved_genres)

    print("\n🚀 Querying your SQL vault for ranked matching results...")
    df_db_suggestions = get_ranked_suggestions_from_db(conn)
    print(df_db_suggestions.head(10))


    print(f"\n🎬 Simulated Watch History:")
    for show in user1.previous_love_shows:
        print(f" -> {show.title} (Cast IDs: {show.cast})")

    for show in user1.previous_like_shows:
        print(f" -> {show.title} (Cast IDs: {show.cast})")

    print("\n--- Top 5 Custom Suggestions Based on User Genres ---")
    recommendations = generate_suggestions(user1.loved_genres, user1.liked_genres, user1.hated_genres, all_shows_database, user1.previous_love_shows, user1.previous_like_shows, top_count=10)
    for idx, (title, genre_set, cast, rating) in enumerate(recommendations, start=1):
        matching_show = next(s for s in all_shows_database if s.title == title)
        print(f"{idx}. {title} | Genres: {genre_set} | Rating: {abs(rating)}")
    
    print("\n--- Top 5 Suggestions Based on Overlapping Cast from History ---")
    cast_recommendations = find_shows_with_cast(user1.previous_love_shows, user1.previous_like_shows, all_shows_database, top_count=5)
    for idx, title in enumerate(cast_recommendations, start=1):
        matching_show = next(s for s in all_shows_database if s.title == title)
        print(f"{idx}. {title} (Cast IDs: {matching_show.cast})")

    conn.close()
