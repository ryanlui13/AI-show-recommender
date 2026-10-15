# split the data
import pandas as pd
import numpy as np
#import seaborn as sns 
#import matplotlib.pyplot as plt 
import sqlite3 
import os 
import json 
from sklearn.ensemble import RandomForestClassifier 
from sklearn.model_selection import train_test_split # 👈 FIXED: Added missing import
from sklearn.feature_extraction.text import CountVectorizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'data', 'recommender.db')

print("🔮 Connecting to your local SQL vault...")
conn = sqlite3.connect(db_path)

# select the query 
query = """
    SELECT m.tconst, m.primaryTitle, m.genres, r.averageRating, r.numVotes, GROUP_CONCAT(p.nconst, ",") AS cast
    FROM movies m
    INNER JOIN ratings r ON m.tconst = r.tconst
    INNER JOIN principals p on m.tconst = p.tconst 
    WHERE r.numVotes >= 10000
    GROUP BY m.tconst;
"""

df_master = pd.read_sql_query(query, conn)
conn.close()

if 'cast' not in df_master.columns:
    df_master['cast'] = "Actor A, Actor B"

def find_genres(database):
    unique_genres = set()
    for genre_string in database.dropna():
        individual_genre = genre_string.split(',')
        for g in individual_genre:
            unique_genres.add(g.strip())
    return unique_genres

def find_cast(database):
    cast_list = set()
    for actor in database.dropna():
        cast_member = actor.split(',')
        for a in cast_member:
            cast_list.add(a.strip())
    return cast_list 

def train_and_recommend(database):
    x_genres = database['genres'].str.get_dummies(sep=',')
    
    vectorizer = CountVectorizer(token_pattern=r'[^,]+', max_features=1500)
    cast_sparse = vectorizer.fit_transform(database['cast'].fillna(''))
    x_cast = pd.DataFrame(
        cast_sparse.toarray(),
        columns= vectorizer.get_feature_names_out(),
        index = database.index,
        dtype = np.uint8 
    )
    
    x_numeric = database[['averageRating', 'numVotes']]

    # 👈 FIXED: Added axis=1 to combine features side-by-side column-wise
    X = pd.concat([x_genres, x_cast, x_numeric], axis=1) 
    y = ((database['averageRating'] >= 7.0) & (database['numVotes'] >= 5000)).astype(int)

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # random forest 
    classification = RandomForestClassifier(n_estimators=50, max_depth=7, random_state=42)
    classification.fit(x_train, y_train)
    
    # 👈 FIXED: Passed the mandatory filename string parameter
    save_tree_to_json(classification.estimators_[0], x_train.columns, "tree.json")

    accuracy = classification.score(x_test, y_test)
    print(f"Training complete! Model accuracy: {accuracy * 100:.2%}")

    # evaluate a specific show
    x_new = x_test.iloc[[0]]
    prediction = classification.predict(x_new)

    show_title = database.iloc[x_test.index[0]]['primaryTitle']
    print(f"🎬 Prediction for '{show_title}': {'🌟 Recommend!' if prediction[0] == 1 else '❌ Skip it.'}")

def save_tree_to_json(model, feature_names, filename):
    # get the internal tree structure from scikit-learn
    tree = model.tree_ 

    # build each node in the tree
    def build_node(node_id):
        # check if the node is a leaf
        if tree.children_left[node_id] == -1 and tree.children_right[node_id] == -1:
            # match diagram classes
            matching_map = {4: "love", 3: "like", 2: "ok", 1: "dislike" , 0: "hate"}
            
            # come up w/ tree prediction 
            raw_predict = int(np.argmax(tree.value[node_id])) 
            return {
                "node_type": "leaf",
                "node_id": int(node_id),
                "prediction": matching_map.get(raw_predict, "love")
            }
        
        # if the node ISN'T a leaf, get the feature + threshold 
        return {
            "node_type": "split",
            "node_id": int(node_id),
            "split_feature": feature_names[tree.feature[node_id]],
            "split_threshold": round(float(tree.threshold[node_id]), 2),

            # keep traversing through the tree (yes) or (no) paths
            "if_less_or_equal": build_node(tree.children_left[node_id]),
            "if_greater": build_node(tree.children_right[node_id])
        }
    
    # full dictionary at root
    full_tree_dict = build_node(0)

    # save the tree to a file 
    with open(filename, "w") as f:
        json.dump(full_tree_dict, f, indent=4)

    print(f"Tree has been exported to {filename}")

def evaluate_show(node, show_data):
    if node["node_type"] == "leaf":
        return node["prediction"]

    feature = node["split_feature"]
    threshold = node["split_threshold"]
    movie_value = show_data.get(feature, 0)

    if movie_value > threshold:
        return evaluate_show(node["if_greater"], show_data)
    else:
        return evaluate_show(node["if_less_or_equal"], show_data)

# 3. Print your data tables to check the matrix structure
print("\n📊 FIRST 5 ROWS OF YOUR DATA ENGINE:")
print(df_master.head())

# 4. Fire your Seaborn visualization to see how your rating/vote splits cluster!
print("\n🎨 Rendering your data distribution visualization...")
#sns.scatterplot(data=df_master.head(1000), x='averageRating', y='numVotes', alpha=0.6)
#plt.title("Visualize Movie Splits for Decision Trees")
#plt.yscale('log') 
#plt.show()

# Fire the training loop!
train_and_recommend(df_master)
