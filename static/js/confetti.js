/**
 * FitBrainLab Confetti Animation
 * Creates a massive confetti explosion when a challenge is completed
 */

// Single global confetti function
function launchConfetti() {
  console.log('🎊 Launching SUPER MASSIVE confetti celebration');
  
  // Clear any previous animations
  if (window.confettiIntervals) {
    window.confettiIntervals.forEach(clearInterval);
  }
  window.confettiIntervals = [];
  
  // Bright, vibrant colors
  const colors = ['#ff6b6b', '#feca57', '#1dd1a1', '#54a0ff', '#5f27cd', '#ff9ff3', '#ffeaa7', '#55efc4'];
  
  // MASSIVE burst from center - even more particles!
  confetti({
    particleCount: 250,  // WAY more particles
    spread: 180,        // Full spread in all directions
    origin: { x: 0.5, y: 0.5 },  // Center of screen
    colors: colors,
    startVelocity: 55,  // Higher velocity
    gravity: 0.6,       // Slightly less gravity for longer hang time
    ticks: 350,         // Longer-lasting confetti
    scalar: 1.8         // Larger particles
  });
  
  // Fire from all corners too - this is what really makes it impressive!
  // Top left
  confetti({
    particleCount: 100,
    angle: 135,
    spread: 90,
    origin: { x: 0, y: 0 },
    colors: colors,
    ticks: 300,
    gravity: 0.6,
    scalar: 1.2
  });
  
  // Top right
  confetti({
    particleCount: 100,
    angle: 45,
    spread: 90,
    origin: { x: 1, y: 0 },
    colors: colors,
    ticks: 300,
    gravity: 0.6,
    scalar: 1.2
  });
  
  // Bottom left
  confetti({
    particleCount: 100,
    angle: 225,
    spread: 90,
    origin: { x: 0, y: 1 },
    colors: colors,
    ticks: 300,
    gravity: 0.6,
    scalar: 1.2
  });
  
  // Bottom right
  confetti({
    particleCount: 100,
    angle: 315,
    spread: 90,
    origin: { x: 1, y: 1 },
    colors: colors,
    ticks: 300,
    gravity: 0.6,
    scalar: 1.2
  });
  
  // Fire from all edges with more particles
  // Top edge
  for (let x = 0; x <= 1; x += 0.2) {
    confetti({
      particleCount: 70,  // More particles
      angle: 90,  // Down
      spread: 80,
      origin: { x: x, y: 0 },
      colors: colors,
      ticks: 300,
      gravity: 0.6,
      scalar: 1.2
    });
  }
  
  // Bottom edge
  for (let x = 0; x <= 1; x += 0.2) {
    confetti({
      particleCount: 70,  // More particles
      angle: 270,  // Up
      spread: 80,
      origin: { x: x, y: 1 },
      colors: colors,
      ticks: 300,
      gravity: 0.6,
      scalar: 1.2
    });
  }
  
  // Left edge
  for (let y = 0; y <= 1; y += 0.2) {
    confetti({
      particleCount: 70,  // More particles
      angle: 0,  // Right
      spread: 80,
      origin: { x: 0, y: y },
      colors: colors,
      ticks: 300,
      gravity: 0.6,
      scalar: 1.2
    });
  }
  
  // Right edge
  for (let y = 0; y <= 1; y += 0.2) {
    confetti({
      particleCount: 70,  // More particles
      angle: 180,  // Left
      spread: 80,
      origin: { x: 1, y: y },
      colors: colors,
      ticks: 300,
      gravity: 0.6,
      scalar: 1.2
    });
  }
  
  // Continue with even more random confetti bursts for 5 seconds
  const duration = 3 * 1000;  // Longer duration
  const end = Date.now() + duration;
  
  // Fire confetti VERY rapidly from random positions
  const interval = setInterval(() => {
    // Random position on the screen
    const x = Math.random();
    const y = Math.random();
    
    confetti({
      particleCount: 40,       // More particles each time
      angle: Math.random() * 360,  // Random angle
      spread: 100,              // Wide spread
      origin: { x, y },
      colors: colors,
      ticks: 300,
      gravity: 0.5,
      scalar: 1.7              // Larger particles
    });
    
    if (Date.now() > end) {
      clearInterval(interval);
    }
  }, 40);  // Even more frequent - fire every 40ms instead of 50ms
  
  window.confettiIntervals.push(interval);
}

// Make sure function is available globally
window.launchConfetti = launchConfetti;
