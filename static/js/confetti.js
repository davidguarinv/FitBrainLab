/**
 * FitBrainLab Confetti Animation
 * Creates a massive confetti explosion when a challenge is completed
 */

// Single global confetti function
function launchConfetti() {
  console.log('🎊 Launching confetti celebration');
  
  // Bright, vibrant colors
  const colors = ['#ff6b6b', '#feca57', '#1dd1a1', '#54a0ff', '#5f27cd', '#ff9ff3', '#ffeaa7', '#55efc4'];
  
  // Fire massive burst from center
  confetti({
    particleCount: 150,  // Tons of particles
    spread: 180,        // Full spread in all directions
    origin: { x: 0.5, y: 0.5 },  // Center of screen
    colors: colors,
    startVelocity: 45,  // High velocity
    gravity: 0.7,       // Regular gravity
    ticks: 300
  });
  
  // Fire from all edges
  // Top edge
  for (let x = 0; x <= 1; x += 0.2) {
    confetti({
      particleCount: 50,
      angle: 90,  // Down
      spread: 80,
      origin: { x: x, y: 0 },
      colors: colors,
      ticks: 250
    });
  }
  
  // Bottom edge
  for (let x = 0; x <= 1; x += 0.2) {
    confetti({
      particleCount: 50,
      angle: 270,  // Up
      spread: 80,
      origin: { x: x, y: 1 },
      colors: colors,
      ticks: 250
    });
  }
  
  // Left edge
  for (let y = 0; y <= 1; y += 0.2) {
    confetti({
      particleCount: 50,
      angle: 0,  // Right
      spread: 80,
      origin: { x: 0, y: y },
      colors: colors,
      ticks: 250
    });
  }
  
  // Right edge
  for (let y = 0; y <= 1; y += 0.2) {
    confetti({
      particleCount: 50,
      angle: 180,  // Left
      spread: 80,
      origin: { x: 1, y: y },
      colors: colors,
      ticks: 250
    });
  }
  
  // Continue with random confetti bursts for 4 seconds
  const duration = 4 * 1000;
  const end = Date.now() + duration;
  
  // Clear any previous intervals
  if (window.confettiInterval) {
    clearInterval(window.confettiInterval);
  }
  
  // Fire confetti rapidly from random positions
  window.confettiInterval = setInterval(() => {
    // Random position on the screen
    const x = Math.random();
    const y = Math.random();
    
    confetti({
      particleCount: 30,       // Lots of particles each time
      angle: Math.random() * 360,  // Random angle
      spread: 100,              // Wide spread
      origin: { x, y },
      colors: colors,
      ticks: 300,
      gravity: 0.5,
      scalar: 1.5              // Larger particles
    });
    
    if (Date.now() > end) {
      clearInterval(window.confettiInterval);
      window.confettiInterval = null;
    }
  }, 50);  // Fire very frequently
}

// Make sure function is available globally
window.launchConfetti = launchConfetti;
