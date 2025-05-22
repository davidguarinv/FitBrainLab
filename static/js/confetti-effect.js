/**
 * Enhanced Confetti Animation for FitBrainLab
 * Version: 1.0.0
 * Date: 2025-05-22
 */

// Make sure confetti library is loaded
if (typeof confetti === 'undefined') {
  console.error('Confetti library not loaded! Loading it now...');
  // Try to load it dynamically if missing
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js';
  script.async = true;
  document.head.appendChild(script);
}

/**
 * Launch an impressive confetti celebration from all sides of the screen
 */
function launchConfetti() {
  console.log('🎉 Launching confetti celebration v1.0.0');
  
  // Configuration
  var duration = 4 * 1000;
  var end = Date.now() + duration;
  var colors = ['#ff6b6b', '#feca57', '#1dd1a1', '#54a0ff', '#5f27cd'];
  
  // Fire immediate burst from all 8 sides
  fireConfettiFromSide(0, 0, 135, colors);       // Top left
  fireConfettiFromSide(0.5, 0, 90, colors);      // Top center
  fireConfettiFromSide(1, 0, 45, colors);        // Top right
  fireConfettiFromSide(0, 0.5, 180, colors);     // Middle left
  fireConfettiFromSide(1, 0.5, 0, colors);       // Middle right
  fireConfettiFromSide(0, 1, 225, colors);       // Bottom left
  fireConfettiFromSide(0.5, 1, 270, colors);     // Bottom center
  fireConfettiFromSide(1, 1, 315, colors);       // Bottom right
  
  // Continue with ongoing confetti for the duration
  var interval = setInterval(function() {
    var randomSide = Math.floor(Math.random() * 8);
    var origins = [
      { x: 0, y: 0 },      // Top left
      { x: 0.5, y: 0 },    // Top center
      { x: 1, y: 0 },      // Top right
      { x: 0, y: 0.5 },    // Middle left
      { x: 1, y: 0.5 },    // Middle right
      { x: 0, y: 1 },      // Bottom left
      { x: 0.5, y: 1 },    // Bottom center
      { x: 1, y: 1 }       // Bottom right
    ];
    
    var angles = [135, 90, 45, 180, 0, 225, 270, 315];
    
    confetti({
      particleCount: 5,
      angle: angles[randomSide],
      spread: 80,
      origin: origins[randomSide],
      colors: colors,
      gravity: 0.1,
      ticks: 450,
      scalar: 1.1,
      drift: 0.2
    });
    
    if (Date.now() > end) {
      clearInterval(interval);
    }
  }, 150);
}

/**
 * Helper function to fire confetti from a specific side
 */
function fireConfettiFromSide(x, y, angle, colors) {
  if (typeof confetti === 'undefined') {
    console.error('Confetti library still not available');
    return;
  }
  
  confetti({
    particleCount: 15,
    angle: angle,
    spread: 90,
    origin: { x: x, y: y },
    colors: colors,
    gravity: 0.2,
    ticks: 500,
    scalar: 1.2,
    drift: (x === 0.5 && y === 0.5) ? 0 : (x > 0.5 ? 0.5 : -0.5)
  });
}

// Make sure the function is globally available
window.launchConfetti = launchConfetti;
