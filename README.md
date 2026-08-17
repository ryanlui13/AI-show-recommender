🧙‍♂️ Wizard of the Show'nanigans — AI Show Recommender

A personalized TV show and movie recommendation system powered by a **FastAPI** backend, custom decision tree logic, and an interactive **HTML/CSS/JS** frontend modal quiz. 

Users can log their favorite genres, previous shows they loved/liked, and cast preferences to receive dynamic recommendations tailored to their taste profile.

---

## 🚀 Features

* **Interactive Profile & Quiz Modal:** Users submit their age, username, preferred/disliked genres, and watch history.
* **Dual Recommendation Engine:**
  * **Genre-based Recommendations:** Generates top show picks by scoring genre preferences against database ratings.
  * **Cast-based Recommendations:** Finds shows sharing key cast members from previously loved and liked shows.
* **Decision Tree Evaluation Engine:** Integrates a decision tree (`tree.json`) to evaluate specific show tiers (e.g., Top Pick, Recommended, or Not Recommended).
* **Local Persistence:** Saves user profile data locally via browser `localStorage`.
* **FastAPI Backend:** Fast REST API handling query matching, data filtering, and recommendation generation.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, JavaScript (ES6+ / Fetch API)
* **Backend:** Python 3.9+, FastAPI, Uvicorn
* **Data Processing & Database:** Pandas, SQLite, `heapq`
* **Machine Learning / Logic:** Custom Decision Tree Classifier (`tree.json`)

---

## 📁 Project Structure

```text
├── data/
│   └── recommender.db           # SQLite database containing movies, ratings, and cast info
├── index_2.html                 # Main frontend UI
├── index.css                    # UI styles and modal rules
├── quizAnswers_3.js             # DOM manipulation, quiz submit logic, API integration
├── fast_api_3.py                # FastAPI endpoints and recommendation pipeline
├── suggestion_generator.py      # Recommendation core logic and User/Show models
├── tree.json                    # Decision tree structure for show evaluation
└── README.md                    # Project documentation
