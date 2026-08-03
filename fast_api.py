from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 
from typing import List
import pandas as pd
import os
import heapq
import sqlite3
import json 

from suggestion_generator import User, generate_suggestions, Shows, find_shows_with_cast 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#read the data from the 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'data', 'recommender.db')
conn = sqlite3.connect(db_path)

query = """
    SELECT m.primaryTitle, m.genres, r.averageRating, r.numVotes, GROUP_CONCAT(p.nconst, ",") AS real_cast
    FROM movies m
    INNER JOIN ratings r ON m.tconst = r.tconst
    LEFT JOIN principals p ON m.tconst = p.tconst AND (p.category = 'actor' OR p.category = 'actress')
    WHERE r.numVotes >= 5000
    GROUP BY m.tconst;
"""
    
df_master = pd.read_sql_query(query, conn)
conn.close()

# Replace all NaN values with safe JSON-serializable fallbacks
df_master = df_master.fillna({
    'primaryTitle': '',
    'genres': '',
    'averageRating': 0.0,
    'numVotes': 0
})
# Or clean any remaining NaN across all columns:
df_master = df_master.where(pd.notnull(df_master), None)

#clearn dataframe
df_master = df_master.fillna("")

show_list = df_master.to_dict(orient="records")

def clean_cast(cast_list):
    if not cast_list: 
        return ["Unknown cast"]

    cleaned = [actor for actor in cast_list if not str(actor).startswith('nm')]
    return cleaned if cleaned else ["Cast unavaliable"]

    
#get the shows list from the files. read data
@app.get("/shows")
def get_all_shows():
    return {"total_count": len(show_list), "shows": show_list}

#quiz format
class QuizAnswer(BaseModel):
    loved_genres: List[str]
    liked_genres: List[str]
    hated_genres: List[str]
    preferences: List[str]
    previous_love_shows: List[str]
    previous_like_shows: List[str]
    min_rating: float
    min_votes: int

all_shows_database = []
for row in df_master.itertuples():
    #split the genre 
    if isinstance(row.genres, str) and row.genres not in ['Unknown', '\\N', '']:
        genre_set = set(row.genres.split(','))
    else:
        genre_set = set()
    
    # Extract cast set from SQL results
    if isinstance(row.real_cast, str) and row.real_cast != '\\N':
        actual_cast_set = set(row.real_cast.split(','))
    else:
        actual_cast_set = set()

    #create the show object
    new_show = Shows(title = row.primaryTitle, genres = genre_set, cast=actual_cast_set, rating=float(row.averageRating))
    all_shows_database.append(new_show)

ACTIVE_USER_SESSIONS = {}

#path to handle submitting the form. 
@app.post("/recommend")
def submit_form(answers: QuizAnswer):
    chosen_rating = answers.min_rating
    userlove_genres = answers.loved_genres
    userlike_genres = answers.liked_genres
    userhate_genres = answers.hated_genres

    userlove_show = answers.previous_love_shows
    userlike_show = answers.previous_like_shows

    current_user = User(user="ryan_coded", age=21)
    current_user.add_genres("love",userlove_genres)
    current_user.add_genres("like",userlike_genres)
    current_user.add_genres("hate",userhate_genres)

    #love show
    for show_title in userlove_show:
        #search shows for a show w/ match title
        matching_show = next((s for s in all_shows_database if s.title.lower() == show_title.lower().strip()), None)
        if matching_show:
            current_user.add_shows("love list", matching_show)
    
    #like show
    for show_title in userlike_show:
        #search shows for a show w/ match title
        matching_show = next((s for s in all_shows_database if s.title.lower() == show_title.lower().strip()), None)
        if matching_show:
            current_user.add_shows("like list", matching_show)

    #call the generate suggestions to add the shows into the list
    suggestions = generate_suggestions(current_user.loved_genres, current_user.liked_genres, current_user.hated_genres, all_shows_database, current_user.previous_love_shows, current_user.previous_like_shows, top_count=10)
    genre_recommendations_list = []
    for title, genres, cast, rating in suggestions:
        genre_recommendations_list.append({
            "title": title,
            "genres": list(genres) if genres else [],
            "cast": list(cast) if cast else [],
            "rating": abs(rating)
        })

    shows_by_title = {s.title: s for s in all_shows_database}

    cast_suggestions = find_shows_with_cast(current_user.previous_love_shows, current_user.previous_like_shows, all_shows_database, top_count=10)
    cast_recommendations_list = []
    for title, genres, cast, rating in cast_suggestions:
        matching_show = shows_by_title.get(title)
        if matching_show:
            cast_recommendations_list.append({
                "title": matching_show.title,
                "genres": list(matching_show.genres) if matching_show.genres else [],                
                "cast": list(matching_show.cast) if matching_show.cast else [],
                "rating": abs(matching_show.rating)
            })

    return {
        "message": f"Here are showes rated above {chosen_rating} based on {userlove_genres}! the list is below....", 
        "user_loved_genres": list(current_user.loved_genres),
        "user_liked_genres": list(current_user.liked_genres),
        "genre_recommendations": genre_recommendations_list,
        "cast_recommendations": cast_recommendations_list
    }

# GET the genres. Returns a sorted list of all unique genres 
@app.get("/genres")
def get_genres():
    # 1. Drop any missing rows, split strings by comma, and "explode" them into one single long series
    all_genres = df_master['genres'].dropna().str.split(',').explode()
    
    # 2. Strip whitespace and filter out any garbage entries like 'Unknown' or empty strings
    clean_genres = all_genres.str.strip()
    clean_genres = clean_genres[clean_genres.str.len() > 0]
    
    # 3. Get unique items, sort them alphabetically, and convert to a standard Python list
    unique_genres_list = sorted(list(clean_genres.unique()))
    
    return {"genres": unique_genres_list}


#get the show search 
@app.get('/shows/search')
def get_show(showTitle):
    showTitle = showTitle.strip()
    #filter data for title
    matching_result = df_master[df_master['primaryTitle'].str.contains(showTitle, case=False, na=False)]

    if matching_result.empty:
        raise HTTPException(status_code=404, detail=f"No shows found matching '{showTitle}'")

    results = matching_result.head(10).to_dict(orient="records")
    return {"search_term": showTitle, "results": results}

#detailed analystics summary
#find most frequent genres in watch history, watched shows and min accepting rating
@app.get("/user/summary")
def get_summary(user_name: str, user_age: int, min_show_rating: float, top_count: int=5):
    lookup_key = user_name.lower().strip()

    if lookup_key not in ACTIVE_USER_SESSIONS:
        raise HTTPException(status_code=404, detail=f"User profile not found for '{user_name}'")
    
    current_user = ACTIVE_USER_SESSIONS[lookup_key]

    genre_counts = {}
    for show in current_user.previous_love_shows:
        #look for shows above rating
        if show.rating >= min_show_rating:
            for genre in show.genres:
                if genre in genre_counts:
                    genre_counts[genre] += 1
                else:
                    genre_counts[genre] = 1
    
    for show in current_user.previous_like_shows:
        #look for shows above rating
        if show.rating >= min_show_rating:
            for genre in show.genres:
                if genre in genre_counts:
                    genre_counts[genre] += 1
                else:
                    genre_counts[genre] = 1
    
    #use heap to keep track of most liked genre. store rating, genre
    genre_heap = [] 

    #look through history
    for genre, count in genre_counts.items():
        heapq.heappush(genre_heap, (-count, genre))

    top_genres = []
    while genre_heap and len(top_genres) < top_count:
        negative_score, genre = heapq.heappop(genre_heap)
        top_genres.append({"genre": genre, "genre_count": abs(negative_score)})
        
    return {
        "username": current_user.user,
        "Top Shows Watched": len(current_user.previous_love_shows),
        "Most liked genres": top_genres
    }

#path route. read from the path
@app.get("/")
def root():
    return {"message": "Welcome to AI show recommender API. Go to /shows to see show data"}

#json user data
@app.post("/user/profile")
def create_profile(user_name: str, user_age: int, answers: QuizAnswer):
    current_user = User(user=user_name, age=user_age)

    current_user.create_profile(
        #genres
        loved_genres= answers.loved_genres,
        liked_genres=answers.liked_genres,
        hated_genres= answers.hated_genres,
        
        #shows
        previous_love_shows= answers.previous_love_shows,
        previous_like_shows= answers.previous_like_shows,
        
        preference_dict={"extra_preferences": answers.preferences, "min_rating": answers.min_rating, "min_votes": answers.min_votes}
    )
    
    ACTIVE_USER_SESSIONS[user_name.lower().strip()] = current_user 

    return {
        "status": "Profile created",
        "user": current_user.user,
        "age": current_user.age,
        "synced_loved_genres": list(current_user.loved_genres),
        "synced_liked_genres": list(current_user.liked_genres),
        "synced_hated_genres": list(current_user.hated_genres)
    }

tree_path = os.path.join(BASE_DIR, "tree.json")
with open(tree_path, "r") as f:
    DECISION_TREE_DATA = json.load(f)

#evaluate the show based on the decision tree and data
def evaluate_show(node, show_data):
    #search the tree 
    if node["node_type"] == "leaf":
        return node["prediction"]

    feature = node["split_feature"]
    threshold = node["split_threshold"]

    #get matching data from show 
    movie_value = show_data.get(feature, 0)
    if movie_value > threshold:
        return evaluate_show(node["if_greater"], show_data)
    else:
        return evaluate_show(node["if_less_or_equal"], show_data)

class ShowEvaluationRequest(BaseModel):
    showTitle: str
    user_loved_genres: List[str]
    user_liked_genres: List[str]
    user_hated_genres: List[str]


#send the recommendations from the tree to api. 
@app.get("/shows/evaluate")
def check_show_tier(request: ShowEvaluationRequest):
    #get input data for show eval 
    showTitle = request.showTitle
    favorite_genres = request.user_loved_genres
    ok_genres = request.user_liked_genres
    bad_genres = request.user_hated_genres
    
    #look through the database for shows.
    show_name = showTitle.strip().lower()
    matching_shows = df_master[df_master['primaryTitle'].str.lower() == show_name]

    if matching_shows.empty:
        raise HTTPException(status_code=404, detail=f"Show '{showTitle}' not found in records.")
    
    #get the first matching show
    show_record = matching_shows.iloc[0].to_dict()

    #genres
    show_genres = show_record.get("genres", "")
    favorite_genre_count = 0
    ok_genre_count = 0
    
    if show_genres:
        current_genres = [g.strip() for g in show_genres.split(",")]
        for genre in current_genres:
            #skip shows w bad genres 
            if genre in bad_genres:
                return {
                    "title": show_record["primaryTitle"],
                    "recommendation level": "❌ Not recommended (Contains genre: " + genre + ")",
                    "What was considered in this decision": "Our Wizzard is saving you from your inner demons!!!"
                }
            #get fav genre count
            elif genre in favorite_genres:
                favorite_genre_count+= 1
            #ok genre count 
            elif genre in ok_genres:
                ok_genre_count += 1
    #cast
    cast_string = show_record.get("cast", "")
    if cast_string:
        cast_count = len(str(cast_string).split(","))
    else:
        cast_count = 0

    genre_score = (2*favorite_genre_count) + ok_genre_count

    show_features = {
        "genreScore": genre_score,
        "averageRating": float(show_record.get("averageRating", 0)),
        "numVotes": int(show_record.get("numVotes", 0)),
        "cast_count": cast_count
    }

    #traverse through tree
    #search through the dictionary, taking in the tree and show features
    leaf_prediction = evaluate_show(DECISION_TREE_DATA, show_features)

    #map the result to recommend tier 
    if leaf_prediction == "love":
        recommendation_tier = "🔥 TOP PICK (Highly Recommended)"
    elif leaf_prediction in ["like", "ok"]:
        recommendation_tier =  "✅ Recommended"
    else:
        recommendation_tier = "Not recommended"
    
    return {
        "title": show_record["primaryTitle"],
        "recommendation level": recommendation_tier,
        "What was considered in this decision": show_features
    }

if __name__ == "__main__":
    genre_list = get_genres()
    for genre in genre_list["genres"]:
        print(f" - {genre}")

    
    print("------------------------------------\n")
