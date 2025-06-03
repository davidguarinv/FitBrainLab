/**
 * Achievement Animation System
 * Handles the display of achievement unlocks with animations and confetti
 */

// Initialize confetti function
function initConfetti() {
    const canvas = document.createElement('canvas');
    canvas.id = 'confetti-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '9999';
    document.body.appendChild(canvas);

    const confetti = window.confetti.create(canvas, {
        resize: true,
        useWorker: true
    });

    return confetti;
}

// Show achievement unlock animation
function showAchievementUnlock(achievement) {
    // Create overlay container
    const overlay = document.createElement('div');
    overlay.id = 'achievement-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.backdropFilter = 'blur(5px)';
    overlay.style.zIndex = '9998';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.5s ease';
    document.body.appendChild(overlay);

    // Create achievement container
    const container = document.createElement('div');
    container.className = 'achievement-container';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.maxWidth = '500px';
    container.style.padding = '2rem';
    container.style.backgroundColor = 'white';
    container.style.borderRadius = '1rem';
    container.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
    container.style.transform = 'translateY(-50px)';
    container.style.opacity = '0';
    container.style.transition = 'transform 0.8s ease, opacity 0.8s ease';
    overlay.appendChild(container);

    // Create achievement icon container
    const iconContainer = document.createElement('div');
    iconContainer.className = 'achievement-icon-container';
    iconContainer.style.marginBottom = '1.5rem';
    iconContainer.style.perspective = '1000px';
    container.appendChild(iconContainer);

    // Create achievement icon
    const icon = document.createElement('div');
    icon.className = 'achievement-icon';
    icon.style.width = '100px';
    icon.style.height = '100px';
    icon.style.backgroundColor = '#f8f9fa';
    icon.style.borderRadius = '50%';
    icon.style.display = 'flex';
    icon.style.justifyContent = 'center';
    icon.style.alignItems = 'center';
    icon.style.transformStyle = 'preserve-3d';
    icon.style.animation = 'spin-and-drop 1.5s ease forwards';
    iconContainer.appendChild(icon);

    // Create SVG icon
    const svgIcon = document.createElement('img');
    svgIcon.src = `/static/images/svg/achievements/${achievement.icon_type}.svg`;
    svgIcon.style.width = '60px';
    svgIcon.style.height = '60px';
    svgIcon.style.color = '#ff6b6b';
    icon.appendChild(svgIcon);

    // Create achievement title
    const title = document.createElement('h2');
    title.textContent = 'Achievement Unlocked!';
    title.style.fontSize = '1.5rem';
    title.style.fontWeight = 'bold';
    title.style.color = '#333';
    title.style.marginBottom = '0.5rem';
    title.style.textAlign = 'center';
    container.appendChild(title);

    // Create achievement name
    const name = document.createElement('h3');
    name.textContent = achievement.name;
    name.style.fontSize = '1.25rem';
    name.style.fontWeight = 'bold';
    name.style.color = '#ff6b6b';
    name.style.marginBottom = '1rem';
    name.style.textAlign = 'center';
    container.appendChild(name);

    // Create achievement condition
    const condition = document.createElement('p');
    condition.textContent = getConditionText(achievement.condition);
    condition.style.fontSize = '1rem';
    condition.style.color = '#666';
    condition.style.marginBottom = '1.5rem';
    condition.style.textAlign = 'center';
    container.appendChild(condition);

    // Create achievement message
    const message = document.createElement('p');
    message.textContent = achievement.message;
    message.style.fontSize = '1rem';
    message.style.color = '#333';
    message.style.marginBottom = '2rem';
    message.style.textAlign = 'center';
    message.style.fontStyle = 'italic';
    container.appendChild(message);

    // Create return button
    const button = document.createElement('button');
    button.textContent = 'Return to FitQuest';
    button.style.padding = '0.75rem 1.5rem';
    button.style.backgroundColor = '#ff6b6b';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '0.5rem';
    button.style.fontSize = '1rem';
    button.style.fontWeight = 'bold';
    button.style.cursor = 'pointer';
    button.style.transition = 'background-color 0.3s ease';
    button.addEventListener('mouseover', () => {
        button.style.backgroundColor = '#ff5252';
    });
    button.addEventListener('mouseout', () => {
        button.style.backgroundColor = '#ff6b6b';
    });
    button.addEventListener('click', () => {
        closeAchievementOverlay(overlay);
    });
    container.appendChild(button);

    // Add animation keyframes
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin-and-drop {
            0% { transform: translateY(-200px) rotateY(0deg); }
            60% { transform: translateY(0) rotateY(1080deg); }
            80% { transform: translateY(-20px) rotateY(1080deg); }
            100% { transform: translateY(0) rotateY(1080deg); }
        }
    `;
    document.head.appendChild(style);

    // Trigger confetti
    const confetti = initConfetti();
    confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.3 }
    });

    // Show overlay with animation
    setTimeout(() => {
        overlay.style.opacity = '1';
    }, 100);

    // Show container with animation
    setTimeout(() => {
        container.style.transform = 'translateY(0)';
        container.style.opacity = '1';
    }, 500);
}

// Close achievement overlay
function closeAchievementOverlay(overlay) {
    overlay.style.opacity = '0';
    setTimeout(() => {
        overlay.remove();
        const canvas = document.getElementById('confetti-canvas');
        if (canvas) canvas.remove();
    }, 500);
}

// Get human-readable condition text
function getConditionText(condition) {
    if (condition.endsWith('_total')) {
        const count = condition.split('_')[0];
        return `Complete ${count} total challenges`;
    } else if (condition.endsWith('_easy')) {
        const count = condition.split('_')[0];
        return `Complete ${count} easy challenges`;
    } else if (condition.endsWith('_medium')) {
        const count = condition.split('_')[0];
        return `Complete ${count} medium challenges`;
    } else if (condition.endsWith('_hard')) {
        const count = condition.split('_')[0];
        return `Complete ${count} hard challenges`;
    } else if (condition.startsWith('points_')) {
        const points = condition.split('_')[1];
        return `Earn ${points} total points`;
    } else if (condition.startsWith('friend_')) {
        const count = condition.split('_')[1];
        return `Complete ${count} friend challenges`;
    } else if (condition.startsWith('habit_')) {
        const count = condition.split('_')[1];
        return `Complete ${count} weekly habit challenges`;
    } else if (condition === 'weekly_all') {
        return 'Complete all weekly challenges';
    } else if (condition.startsWith('streak_')) {
        const days = condition.split('_')[1];
        return `Maintain a ${days}-day streak`;
    }
    return condition;
}

// Export functions for global use
window.showAchievementUnlock = showAchievementUnlock;
