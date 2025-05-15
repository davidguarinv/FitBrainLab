// OutBurst Game Logic
// Handles tab switching, rendering of each section: progress, challenges, leaderboard, profile

// State management
const state = {
    challenges: {
        inProgress: [],
        available: []
    },
    leaderboard: [],
    weekProgress: [],
    completedDays: [],
    userProfile: null
};

// Utility to format Monday-based week
function getWeekDates(offsetWeeks = 0) {
    const now = new Date();
    const day = now.getDay(); // 0=Sun,1=Mon...
    const monday = new Date(now);
    const diff = (day + 6) % 7; // days since Monday
    monday.setDate(now.getDate() - diff + offsetWeeks * 7);
    return Array.from({ length: 7 }).map((_, i) => {
        const d = new Date(monday);
        d.setDate(monday.getDate() + i);
        return d;
    });
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        content.classList.add('hidden');
    });

    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });

    // Show selected tab content and activate button
    document.getElementById(tabName + 'Content').classList.remove('hidden');
    document.getElementById(tabName + 'Content').classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Load tab-specific content
    if (tabName === 'leaderboard') loadLeaderboard();
    else if (tabName === 'progress') loadProgress();
    else if (tabName === 'challenges') loadChallenges();
    else if (tabName === 'profile') loadProfile();
}

// Load leaderboard data
function loadLeaderboard() {
    fetch('/api/leaderboard')
        .then(response => response.json())
        .then(data => {
            const leaderboardList = document.getElementById('leaderboardList');
            if (!leaderboardList) return;

            leaderboardList.innerHTML = data.map((user, index) => `
                <div class="leaderboard-item">
                    <div class="flex items-center space-x-3">
                        <span class="leaderboard-rank">#${index + 1}</span>
                        <span class="text-gray-900">${user.username}</span>
                    </div>
                    <span class="leaderboard-points">${user.points} points</span>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading leaderboard:', error));
}

// Load public leaderboard for landing page
function loadPublicLeaderboard() {
    fetch('/api/leaderboard/public')
        .then(response => response.json())
        .then(data => {
            const publicLeaderboard = document.getElementById('publicLeaderboard');
            if (!publicLeaderboard) return;

            publicLeaderboard.innerHTML = data.map((user, index) => `
                <div class="leaderboard-item">
                    <div class="flex items-center space-x-3">
                        <span class="leaderboard-rank">#${index + 1}</span>
                        <span class="text-gray-900">${user.username}</span>
                    </div>
                    <span class="leaderboard-points">${user.points} points</span>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading public leaderboard:', error));
}

// Load user progress
function loadProgress() {
    fetch('/api/progress')
        .then(response => response.json())
        .then(data => {
            const progressStats = document.getElementById('progressStats');
            if (!progressStats) return;

            progressStats.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Total Points</h3>
                    <p class="mt-2 text-3xl font-semibold text-primary">${data.totalPoints}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Challenges Completed</h3>
                    <p class="mt-2 text-3xl font-semibold text-primary">${data.completedChallenges}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 class="text-lg font-medium text-gray-900">Current Streak</h3>
                    <p class="mt-2 text-3xl font-semibold text-primary">${data.currentStreak} days</p>
                </div>
            `;

            // Update calendar
            const calendar = document.getElementById('progressCalendar');
            if (calendar) {
                calendar.innerHTML = generateCalendar(data.completedDates);
            }
        })
        .catch(error => console.error('Error loading progress:', error));
}

// Load challenges
async function loadChallenges() {
    try {
        const response = await fetch('/api/challenges');
        const data = await response.json();
        state.challenges = data;
        renderChallenges();
    } catch (error) {
        console.error('Error loading challenges:', error);
    }
}

// Render challenges
function renderChallenges() {
    const challengesList = document.getElementById('challengesList');
    const inProgressSection = document.getElementById('inProgressChallenges');
    if (!challengesList || !inProgressSection) return;

    // Clear existing content
    challengesList.innerHTML = '';
    inProgressSection.innerHTML = '';

    // Render in-progress challenges first
    if (state.challenges.in_progress.length > 0) {
        inProgressSection.innerHTML = `
            <h3 class="text-xl font-semibold text-gray-900 mb-4">In Progress</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${state.challenges.in_progress.map(challenge => createChallengeCard(challenge, true)).join('')}
            </div>
        `;
    }

    // Render available challenges
    challengesList.innerHTML = state.challenges.available.map(challenge => 
        createChallengeCard(challenge, false)
    ).join('');
}

// Create challenge card
function createChallengeCard(challenge, isInProgress) {
    const difficultyColors = {
        'E': 'bg-green-100 text-green-800',
        'M': 'bg-yellow-100 text-yellow-800',
        'H': 'bg-red-100 text-red-800'
    };

    const difficultyLabels = {
        'E': 'Easy',
        'M': 'Medium',
        'H': 'Hard'
    };

    return `
        <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200 h-full flex flex-col">
            <div class="flex justify-between items-start mb-4">
                <h4 class="text-lg font-semibold text-gray-900">${challenge.title}</h4>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${difficultyColors[challenge.diff]}">
                    ${difficultyLabels[challenge.diff]}
                </span>
            </div>
            <p class="text-gray-600 mb-6 flex-grow">${challenge.desc}</p>
            <div class="flex items-center justify-between mt-auto">
                <span class="text-sm font-medium text-gray-900">${challenge.points} points</span>
                ${isInProgress ? `
                    <div class="space-x-2">
                        <button onclick="completeChallenge(${challenge.id})" class="px-3 py-1 bg-primary text-white text-sm font-medium rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                            Complete
                        </button>
                        <button onclick="forfeitChallenge(${challenge.id})" class="px-3 py-1 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                            Forfeit
                        </button>
                    </div>
                ` : `
                    <button onclick="acceptChallenge(${challenge.id})" class="px-3 py-1 bg-primary text-white text-sm font-medium rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                        Accept
                    </button>
                `}
            </div>
        </div>
    `;
}

// Challenge actions
async function acceptChallenge(challengeId) {
    try {
        const response = await fetch(`/api/challenges/${challengeId}/assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            loadChallenges(); // Refresh challenges
        } else {
            const data = await response.json();
            alert(data.msg || 'Error accepting challenge');
        }
    } catch (error) {
        console.error('Error accepting challenge:', error);
    }
}

async function completeChallenge(challengeId) {
    try {
        const response = await fetch(`/api/challenges/${challengeId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            // Show confetti animation
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
            loadChallenges(); // Refresh challenges
            loadProgress(); // Update progress
        }
    } catch (error) {
        console.error('Error completing challenge:', error);
    }
}

async function forfeitChallenge(challengeId) {
    if (!confirm('Are you sure you want to forfeit this challenge?')) return;
    
    try {
        const response = await fetch(`/api/challenges/${challengeId}/forfeit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            loadChallenges(); // Refresh challenges
        }
    } catch (error) {
        console.error('Error forfeiting challenge:', error);
    }
}

// Load leaderboard
async function loadLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard');
        const data = await response.json();
        state.leaderboard = data.board;
        renderLeaderboard();
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// Render leaderboard
function renderLeaderboard() {
    const leaderboardList = document.getElementById('leaderboardList');
    if (!leaderboardList) return;

    leaderboardList.innerHTML = state.leaderboard.map((user, index) => `
        <div class="flex items-center justify-between p-3 ${index % 2 === 0 ? 'bg-gray-50' : 'bg-white'} rounded-lg">
            <div class="flex items-center space-x-3">
                <span class="w-6 h-6 flex items-center justify-center ${index < 3 ? 'bg-primary text-white' : 'bg-gray-200 text-gray-700'} rounded-full text-sm font-medium">
                    ${index + 1}
                </span>
                <span class="font-medium text-gray-900">${user.username}</span>
            </div>
            <span class="text-gray-600">${user.pts} points</span>
        </div>
    `).join('');
}

// Load user profile
function loadProfile() {
    fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            const profileInfo = document.getElementById('profileInfo');
            if (!profileInfo) return;

            profileInfo.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="space-y-4">
                        <div>
                            <h3 class="text-lg font-medium text-gray-900">Username</h3>
                            <p class="mt-1 text-gray-600">${data.username}</p>
                        </div>
                        <div>
                            <h3 class="text-lg font-medium text-gray-900">Join Date</h3>
                            <p class="mt-1 text-gray-600">${new Date(data.joinDate).toLocaleDateString()}</p>
                        </div>
                        <div>
                            <h3 class="text-lg font-medium text-gray-900">Achievement Level</h3>
                            <p class="mt-1 text-gray-600">${data.level}</p>
                        </div>
                    </div>
                </div>
            `;
        })
        .catch(error => console.error('Error loading profile:', error));
}

// Load progress
async function loadProgress() {
    try {
        const response = await fetch('/api/progress');
        const data = await response.json();
        state.weekProgress = data.week;
        renderProgress(data.total);
    } catch (error) {
        console.error('Error loading progress:', error);
    }
}

// Render progress
function renderProgress(totalPoints) {
    const weekDays = document.getElementById('weekDays');
    const totalPointsElement = document.getElementById('totalPoints');
    if (!weekDays || !totalPointsElement) return;

    // Update total points
    totalPointsElement.textContent = totalPoints;

    // Get current week dates
    const dates = getWeekDates();
    const today = new Date().toISOString().split('T')[0];

    // Create week day circles
    weekDays.innerHTML = dates.map((date, index) => {
        const dateStr = date.toISOString().split('T')[0];
        const dayName = date.toLocaleString('en-US', { weekday: 'short' });
        const dayNum = date.getDate();
        const isToday = dateStr === today;
        const hasActivity = state.weekProgress.some(day => day.day === dateStr && day.count > 0);

        return `
            <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-full ${hasActivity ? 'bg-primary' : 'bg-gray-200'} ${isToday ? 'ring-2 ring-primary ring-offset-2' : ''} flex items-center justify-center">
                    <div class="text-center">
                        <div class="text-xs font-medium ${hasActivity ? 'text-white' : 'text-gray-600'}">${dayName[0]}</div>
                        <div class="text-sm font-bold ${hasActivity ? 'text-white' : 'text-gray-700'}">${dayNum}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Load profile
async function loadProfile() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        state.userProfile = data;
        renderProfile();
    } catch (error) {
        console.error('Error loading profile:', error);
    }
}

// Render profile
function renderProfile() {
    if (!state.userProfile) return;

    // Update visibility toggle
    document.getElementById('publicProfile').checked = state.userProfile.public;

    // Update top sport
    document.getElementById('topSport').value = state.userProfile.top_sport || '';
}

// Profile actions
async function updateVisibility(isPublic) {
    try {
        const response = await fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ public: isPublic })
        });
        if (!response.ok) throw new Error('Failed to update visibility');
    } catch (error) {
        console.error('Error updating visibility:', error);
        document.getElementById('publicProfile').checked = !isPublic;
    }
}

async function updateTopSport(sport) {
    try {
        const response = await fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ top_sport: sport })
        });
        const data = await response.json();
        if (!response.ok) {
            document.getElementById('sportUpdateMessage').textContent = 'Can only update once per month';
            document.getElementById('topSport').value = state.userProfile.top_sport || '';
        }
    } catch (error) {
        console.error('Error updating top sport:', error);
    }
}

async function updatePassword(event) {
    event.preventDefault();
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        alert('Passwords do not match');
        return;
    }

    try {
        const response = await fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: newPassword })
        });
        if (response.ok) {
            alert('Password updated successfully');
            document.getElementById('passwordForm').reset();
        }
    } catch (error) {
        console.error('Error updating password:', error);
    }
}

async function deleteAccount() {
    if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) return;

    try {
        const response = await fetch('/api/profile/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('Error deleting account:', error);
    }
}

// Helper function to generate calendar
function generateCalendar(completedDates) {
    const today = new Date();
    const calendar = document.createElement('div');
    calendar.className = 'grid grid-cols-7 gap-2';

    // Add day labels
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        const dayLabel = document.createElement('div');
        dayLabel.className = 'text-center text-sm font-medium text-gray-500';
        dayLabel.textContent = day;
        calendar.appendChild(dayLabel);
    });

    // Add calendar days
    const start = new Date(today);
    start.setDate(today.getDate() - 27); // Show last 4 weeks

    for (let i = 0; i < 28; i++) {
        const date = new Date(start);
        date.setDate(start.getDate() + i);
        
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        if (completedDates.includes(date.toISOString().split('T')[0])) {
            dayElement.classList.add('completed');
        }
        
        if (date.toDateString() === today.toDateString()) {
            dayElement.classList.add('today');
        }
        
        dayElement.textContent = date.getDate();
        calendar.appendChild(dayElement);
    }

    return calendar.outerHTML;
}

// Initialize the game page
document.addEventListener('DOMContentLoaded', function() {
    // Load public leaderboard for landing page
    if (document.getElementById('publicLeaderboard')) {
        loadPublicLeaderboard();
    }
    
    // Load initial tab content for authenticated users
    if (document.querySelector('.tab-button')) {
        switchTab('leaderboard');
    }
});
