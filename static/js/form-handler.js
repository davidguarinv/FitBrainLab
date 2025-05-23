// Form submission handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('Form handler initialized');
    
    // Handle application form submission
    const applicationForm = document.querySelector('form[action="/submit-application"]');
    if (applicationForm) {
        console.log('Found application form');
        applicationForm.addEventListener('submit', async function(e) {
            console.log('Form submitted');
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
                console.log(`Form field: ${key} = ${value}`);
            }

            try {
                console.log('Creating form data object');
                const formData = new FormData();
                Object.entries(data).forEach(([key, value]) => {
                    formData.append(key, value);
                });

                console.log('Sending request to server');
                const response = await fetch('/submit-application', {
                    method: 'POST',
                    body: formData
                });

                console.log('Got response, checking status:', response.status);
                const result = await response.json();
                
                console.log('Server response:', result);
                if (!response.ok) {
                    console.error('Server response error:', result);
                    throw new Error(result.message || 'Server error occurred');
                }

                if (result.success) {
                    // Show success message
                    console.log('Showing success message');
                    showMessage(result.message, 'success', applicationForm);
                    // Clear the form
                    this.reset();
                } else {
                    // Show error message
                    console.log('Showing error message');
                    showMessage(result.message || 'Failed to submit application. Please try again.', 'error', applicationForm);
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('An error occurred. Please try again.', 'error', applicationForm);
            }
        });
    } else {
        console.error('Application form not found');
    }

    // Handle community form submission
    const communityForm = document.querySelector('form[action="/submit_community"]');
    if (communityForm) {
        console.log('Found community form');
        communityForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }

            try {
                const response = await fetch('/submit_community', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    // Show success message
                    showMessage(result.message, 'success', communityForm);
                    // Clear the form
                    this.reset();
                } else {
                    // Show error message
                    showMessage(result.message || 'An error occurred. Please try again.', 'error', communityForm);
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('An error occurred. Please try again.', 'error', communityForm);
            }
        });
    }
});

// Helper functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showMessage(message, type, form) {
    // Remove existing messages
    const existingMessage = document.querySelector('.form-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `form-message p-4 rounded-md mb-4 ${type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`;
    messageDiv.textContent = message;
    
    // Insert message before the form
    if (form && form.parentNode) {
        form.parentNode.insertBefore(messageDiv, form);
        
        // Auto-remove success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 5000);
        }
        
        // Scroll to message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
};