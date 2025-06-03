/**
 * Achievement Presentation System
 * Handles the presentation of achievements with animations and effects
 */

// Function to present an achievement to the user
function presentAchievement(achievement) {
    // Create the modal container
    const modalContainer = document.createElement('div');
    modalContainer.id = 'achievement-modal';
    modalContainer.className = 'fixed inset-0 z-50 flex items-center justify-center overflow-auto bg-black bg-opacity-50 backdrop-blur-sm';
    
    // Create the modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'relative flex flex-col items-center justify-center h-full w-full';
    
    // Create the achievement icon container with animation
    const iconContainer = document.createElement('div');
    iconContainer.className = 'relative mb-6 achievement-icon-container';
    
    // Create the SVG icon with animation
    const icon = document.createElement('img');
    icon.src = `/static/images/svg/achievements/${achievement.icon_type}.svg`;
    icon.alt = achievement.name;
    icon.className = 'w-32 h-32 achievement-icon';
    
    // Add the icon to its container
    iconContainer.appendChild(icon);
    
    // Create the text container (initially hidden)
    const textContainer = document.createElement('div');
    textContainer.className = 'text-center achievement-text opacity-0';
    
    // Achievement name and condition
    const nameElement = document.createElement('h3');
    nameElement.className = 'text-2xl font-bold text-white mb-2';
    nameElement.textContent = achievement.name;
    
    // Achievement condition
    const conditionElement = document.createElement('p');
    conditionElement.className = 'text-lg text-white mb-4';
    conditionElement.textContent = `Achievement Unlocked: ${getConditionText(achievement.condition)}`;
    
    // Achievement message
    const messageElement = document.createElement('p');
    messageElement.className = 'text-white text-lg mb-8';
    messageElement.textContent = achievement.message;
    
    // Return button
    const returnButton = document.createElement('button');
    returnButton.className = 'px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-md transition-colors';
    returnButton.textContent = 'Return to FitQuest';
    
    // Add event listener to close the modal
    returnButton.addEventListener('click', () => {
        // Add fade-out animation
        modalContainer.classList.add('opacity-0');
        setTimeout(() => {
            document.body.removeChild(modalContainer);
        }, 500);
    });
    
    // Append all elements to their containers
    textContainer.appendChild(nameElement);
    textContainer.appendChild(conditionElement);
    textContainer.appendChild(messageElement);
    textContainer.appendChild(returnButton);
    
    modalContent.appendChild(iconContainer);
    modalContent.appendChild(textContainer);
    modalContainer.appendChild(modalContent);
    
    // Add the modal to the body
    document.body.appendChild(modalContainer);
    
    // Start the confetti animation
    launchConfetti();
    
    // Start the animation sequence
    setTimeout(() => {
        // Add animation classes to start the animations
        iconContainer.classList.add('animate-achievement-icon');
        
        // Show the text after the icon animation is mostly complete
        setTimeout(() => {
            textContainer.classList.remove('opacity-0');
            textContainer.classList.add('animate-fade-in');
        }, 1500);
    }, 100);
}

// Helper function to get human-readable condition text
function getConditionText(condition) {
    if (condition === 'friend_10') {
        return 'Completed 10 friend challenges';
    } else if (condition.endsWith('_total')) {
        const count = condition.split('_')[0];
        return `Completed ${count} total challenges`;
    } else if (condition.endsWith('_easy')) {
        const count = condition.split('_')[0];
        return `Completed ${count} easy challenges`;
    } else if (condition.endsWith('_medium')) {
        const count = condition.split('_')[0];
        return `Completed ${count} medium challenges`;
    } else if (condition.endsWith('_hard')) {
        const count = condition.split('_')[0];
        return `Completed ${count} hard challenges`;
    } else if (condition.startsWith('points_')) {
        const points = condition.split('_')[1];
        return `Earned ${points} points`;
    }
    return 'Achievement unlocked!';
}

// Function to check for new achievements and present them
function checkAndPresentAchievements() {
    // Check if there are new achievements in the session
    const newAchievementElement = document.getElementById('new-achievement-data');
    if (newAchievementElement) {
        try {
            const achievementData = JSON.parse(newAchievementElement.textContent);
            if (achievementData) {
                // Remove the element to prevent showing the achievement again on refresh
                newAchievementElement.remove();
                
                // Present the achievement
                presentAchievement(achievementData);
            }
        } catch (e) {
            console.error('Error parsing achievement data:', e);
        }
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkAndPresentAchievements();
});
