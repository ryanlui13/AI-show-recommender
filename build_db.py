import sqlite3
import pandas as pd
import os

# Dynamically calculate the base directory path of this specific file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(BASE_DIR, 'data')
db_path = os.path.join(data_dir, 'recommender.db')
basics_tsv_path = os.path.join(data_dir, 'title.basics.tsv.gz')
ratings_tsv_path = os.path.join(data_dir, 'title.ratings.tsv.gz')
principals_tsv_path = os.path.join(data_dir, 'title.principals.tsv.gz')

print("⏳ Step 1: Creating 'data' directory on your drive...")
os.makedirs(data_dir, exist_ok=True)

# Connect to the local database file using the absolute path
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# OPTIMIZATION: Tell SQLite to use RAM for temp storage and turn off heavy journaling
cursor.execute("PRAGMA temp_store = MEMORY;")
cursor.execute("PRAGMA journal_mode = OFF;")

# Custom insertion method for duplicate key handling
def insert_ignore(pd_table, conn, keys, data_iter):
    conn.executemany(
        f"INSERT OR IGNORE INTO {pd_table.name} ({', '.join(keys)}) VALUES ({', '.join(['?']*len(keys))})", 
        data_iter
    )

# =====================================================================
# PHASE 1: BUILD THE MOVIES TABLE (From title.basics.tsv)
# =====================================================================
print("\n📐 Step 2: Defining the 'rating' sql table structure")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    tconst TEXT PRIMARY KEY,
    averageRating REAL,
    numVotes INTEGER
)
""")
conn.commit()

print("⚡ Step 3: Streaming 'title.ratings.tsv.gz' into SQL in small chunks...")
valid_tconsts = set()
for chunk in pd.read_csv(ratings_tsv_path, sep='\t', chunksize=20000, low_memory=False):
    chunk['numVotes'] = pd.to_numeric(chunk['numVotes'], errors='coerce').fillna(0)
    chunk = chunk[chunk['numVotes'] >= 1000]

    if chunk.empty:
        continue 

    valid_tconsts.update(chunk['tconst'].to_list())

    # Using 'to_sql' with a method that tells SQLite to ignore duplicate keys on conflict
    chunk.to_sql(
        'ratings', 
        conn, 
        if_exists='append', 
        index=False, 
        method=insert_ignore
    )

print(f"✅ Found {len(valid_tconsts)} titles with at least 10,000 votes!")

# =====================================================================
# PHASE 2: BUILD THE RATINGS TABLE (From title.ratings.tsv)
# =====================================================================
print("\n📐 Step 4: Defining the 'movies' SQL Table structure...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    tconst TEXT PRIMARY KEY,
    titleType TEXT,
    primaryTitle TEXT,
    originalTitle TEXT,
    isAdult INTEGER,
    startYear INTEGER,
    endYear INTEGER,
    runtimeMinutes INTEGER,
    genres TEXT
)
""")
conn.commit()

print("⚡ Step 5: Streaming 'title.basicss.tsv.gz' into SQL...")
for chunk in pd.read_csv(basics_tsv_path, sep='\t', chunksize=20000, low_memory=False):
    # Doing the same 'INSERT OR IGNORE' trick for the ratings data
    valid_types = ['movie', 'tvSeries', 'tvMiniSeries']
    chunk = chunk[(chunk['titleType'].isin(valid_types)) & (chunk['tconst'].isin(valid_tconsts))] 

    if chunk.empty:
        continue 

    chunk.to_sql(
        'movies', 
        conn, 
        if_exists='append', 
        index=False, 
        method=insert_ignore
    )

# =====================================================================
# PHASE 3: BUILD THE PRINCIPALS TABLE (From title.principals.tsv.gz)
# =====================================================================
print("\n📐 Step 6: Defining the 'principals' SQL Table structure...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS principals (
    tconst TEXT,
    ordering INTEGER,
    nconst TEXT,
    category TEXT,
    job TEXT,
    characters TEXT
)
""")
conn.commit()

print("⚡ Step 7: Streaming 'title.principals.tsv.gz' into SQL (Filtering for Actors)...")
count = 0

for chunk in pd.read_csv(principals_tsv_path, sep='\t', chunksize=50000, low_memory=False):
    # Keep only rows where the category is an actor or actress
    valid_categories = ['actor', 'actress']
    chunk = chunk[chunk['category'].isin(valid_categories) & (chunk['tconst'].isin(valid_tconsts))]

    if chunk.empty:
        continue 
    
    # Append the filtered chunk directly into your SQLite database
    chunk.to_sql('principals', conn, if_exists='append', index=False)
    
    # Print a live tracker so you can see it working!
    count += len(chunk)
    print(f"   Stored {count} valid actor rows so far...", end="\r")

# 🌟 CRITICAL CHANGE: Build the index AFTER the data is completely finished loading!
print("\n📐 Step 8: Optimizing database indexing for high-speed queries...")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_principals_tconst ON principals(tconst);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_principals_nconst ON principals(nconst);")
conn.commit()

print("\n🎉 DATABASE BUILD COMPLETE!")
conn.close()
