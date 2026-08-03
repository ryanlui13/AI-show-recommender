// Get DOM elements
const quiz = document.getElementById('quiz');
const createAccountButton = document.getElementById('createAccount');
const closeQuiz = document.getElementById('close-quiz-btn');
const quizForm = document.getElementById('quiz-form');

const profileUsername = document.getElementById('profile-username');
const profileAge = document.getElementById('profile-age');
const loveCell = document.getElementById('profile-love-genres');
const likeCell = document.getElementById('profile-like-genres');
const hateCell = document.getElementById('profile-hate-genres');

const previousLove_shows = document.getElementById('profile-loved-shows');
const previousLike_shows = document.getElementById('profile-liked-shows');

// Function to load profile from localStorage on page refresh
function loadSavedProfile() {
    const savedData = localStorage.getItem('userProfileData');
    if (!savedData) return; 

    const data = JSON.parse(savedData);

    // Profile data
    if (profileUsername) profileUsername.textContent = data.userName || "No name yet";
    if (profileAge) profileAge.textContent = data.age || "Age not determined"; 
    
    // Genres & Shows - pull directly from 'data' object!
    if (loveCell) loveCell.textContent = data.loveGenres && data.loveGenres.length > 0 ? data.loveGenres.join(', ') : '-';
    if (likeCell) likeCell.textContent = data.likeGenres && data.likeGenres.length > 0 ? data.likeGenres.join(', ') : '-';
    if (hateCell) hateCell.textContent = data.hateGenres && data.hateGenres.length > 0 ? data.hateGenres.join(', ') : '-';
    if (previousLove_shows) previousLove_shows.textContent = data.loveShows && data.loveShows.length > 0 ? data.loveShows.join(', ') : '-';
    if (previousLike_shows) previousLike_shows.textContent = data.likeShows && data.likeShows.length > 0 ? data.likeShows.join(', ') : '-';
}

window.addEventListener('DOMContentLoaded', loadSavedProfile);

// Modal toggle listeners
if (createAccountButton) {
    createAccountButton.addEventListener('click', () => {
        if (quizForm) quizForm.reset();
        quiz.className = 'show-modal';
    });
}

if (closeQuiz) {
    closeQuiz.addEventListener('click', () => {
        quiz.className = 'hidden-modal';
    });
}

//load data from table 
//genres 
function displayGenreRecommendations(recommendations) {
    const tableBody = document.getElementById('genre-recommendations');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No genre recommendations found.</td></tr>';
        return;
    }

    recommendations.forEach((show, index) => {
        const row = document.createElement('tr');
        const genresText = Array.isArray(show.genres) && show.genres.length > 0 ? show.genres.join(', ') : (show.genres || '-');
        
        row.innerHTML = `
                <td>${index + 1}</td>
                <td>${show.title || 'N/A'}</td>
                <td>${genresText}</td>
                <td>${show.rating || '-'}</td>
        `;
        tableBody.appendChild(row);
    });
}

//Cast Recommendations
function displayCastRecommendations(recommendations) {
    const tableBody = document.getElementById('cast-recommendations');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No cast recommendations found.</td></tr>';
        return;
    }

    recommendations.forEach((show, index) => {
        const row = document.createElement('tr');
        const genresText = Array.isArray(show.genres) && show.genres.length > 0 ? show.genres.join(', ') : (show.genres || '-');
        

        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${show.title || show.name || 'N/A'}</td>
            <td>${genresText}</td>
            <td>${show.rating || show.score || '-'}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Submit Quiz
const submitButton = document.getElementById('submit-quiz-btn');
if (submitButton) {
    submitButton.addEventListener("click", async () => {
        const userName_data = document.getElementById('user-name-input')?.value || "";
        const age_data = document.getElementById('user-age-input')?.value || "";
        const previous_love_show_data = document.getElementById('previous-love-shows')?.value || "";
        const previous_like_show_data = document.getElementById('previous-like-shows')?.value || ""; 

        let love = [];
        let like = [];
        let hate = []; 

        document.querySelectorAll('input[type="checkbox"]:checked').forEach(box => {
            if (box.value === 'love') love.push(box.name);
            if (box.value === 'like') like.push(box.name);
            if (box.value === 'hate') hate.push(box.name);
        });

        let profileLoveShows = previous_love_show_data ? previous_love_show_data.split(',').map(show => show.trim()).filter(Boolean) : [];
        let profileLikeShows = previous_like_show_data ? previous_like_show_data.split(',').map(show => show.trim()).filter(Boolean) : [];

        // Save profile object in browser
        const userProfileData = {
            userName: userName_data,
            age: age_data,
            loveGenres: love,
            likeGenres: like,
            hateGenres: hate,
            loveShows: profileLoveShows,
            likeShows: profileLikeShows    
        };

        localStorage.setItem('userProfileData', JSON.stringify(userProfileData));
        loadSavedProfile();

        if (quizForm) quizForm.reset();

        const quizPayload = {
            loved_genres: love,
            liked_genres: like,
            hated_genres: hate,
            preferences: ["Fast-paced"], 
            previous_love_shows: profileLoveShows,
            previous_like_shows: profileLikeShows,
            min_rating: 7.0,
            min_votes: 5000 
        };

        //genre recs
        try {
            const response = await fetch('http://127.0.0.1:8000/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(quizPayload)
            });
            console.log("2️⃣ Response Status Code:", response.status);

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            console.log("🚀 Recommendations received from FastAPI:", data);
            console.log("4️⃣ Genre Recs array:", data.genre_recommendations);
            console.log("5️⃣ Cast Recs array:", data.cast_recommendations);

            displayGenreRecommendations(data.genre_recommendations);
            displayCastRecommendations(data.cast_recommendations);

        } catch (error) {
            console.error("❌ Error sending quiz answers to backend:", error);
        }

        quiz.className = 'hidden-modal';
    });
}

