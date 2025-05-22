// MASSIVE confetti explosion everywhere
function debugConfetti() {
  console.log('🎊 MASSIVE CONFETTI EXPLOSION ACTIVATED');
  
  // Clear any previous animations
  if (window.activeConfettiIntervals) {
    window.activeConfettiIntervals.forEach(clearInterval);
  }
  window.activeConfettiIntervals = [];
  
  // Bright, vibrant colors
  const colors = ['#ff6b6b', '#feca57', '#1dd1a1', '#54a0ff', '#5f27cd', '#ff9ff3', '#ffeaa7', '#55efc4'];
  
  // Create a confetti cannon that fires everywhere
  function fireConfettiCannon() {
    // Fire a MASSIVE burst from center
    confetti({
      particleCount: 150,  // Tons of particles
      spread: 180,        // Full spread in all directions
      origin: { x: 0.5, y: 0.5 },  // Center of screen
      colors: colors,
      startVelocity: 45,  // High velocity
      gravity: 0.7,       // Regular gravity
      ticks: 300
    });
    
    // Fire from all corners and edges
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
  }
  
  // Initial MASSIVE explosion
  fireConfettiCannon();
  
  // Continue with LOTS of confetti for 4 seconds
  const duration = 4 * 1000;
  const end = Date.now() + duration;
  
  // Fire confetti rapidly from random positions
  const interval = setInterval(() => {
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
      clearInterval(interval);
    }
  }, 50);  // Fire very frequently
  
  window.activeConfettiIntervals.push(interval);
  
  // Override the original function to make sure it uses this implementation
  window.launchConfetti = debugConfetti;
}

// Expose the debug function globally
window.debugConfetti = debugConfetti;

// Replace the original launchConfetti with our debug version
window.launchConfetti = debugConfetti;

// Add a button to manually test confetti
document.addEventListener('DOMContentLoaded', function() {
  // Create a small floating button for testing
  const testButton = document.createElement('button');
  testButton.textContent = '🎊 Test Confetti';
  testButton.style.position = 'fixed';
  testButton.style.bottom = '20px';
  testButton.style.right = '20px';
  testButton.style.zIndex = '9999';
  testButton.style.padding = '10px';
  testButton.style.backgroundColor = '#ff6b6b';
  testButton.style.color = 'white';
  testButton.style.border = 'none';
  testButton.style.borderRadius = '4px';
  testButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
  testButton.style.cursor = 'pointer';
  
  // Add click event to test confetti
  testButton.addEventListener('click', function() {
    debugConfetti();
  });
  
  // Add to document
  document.body.appendChild(testButton);
});
