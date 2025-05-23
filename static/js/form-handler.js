// Form submission handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitButton = document.querySelector('button[type="submit"], button:contains("Submit Application")');
    
    // Find the submit button more reliably
    const actualSubmitButton = document.querySelector('button') || 
                              Array.from(document.querySelectorAll('button')).find(btn => 
                                  btn.textContent.includes('Submit'));
    
    if (form && actualSubmitButton) {
        // Prevent default form submission
        actualSubmitButton.addEventListener('click', function(e) {
            e.preventDefault();
            submitForm();
        });
        
        // Also handle form submission event
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm();
        });
    }
    
    function submitForm() {
        // Get form data
        const formData = new FormData();
        formData.append('first_name', document.getElementById('first-name').value);
        formData.append('last_name', document.getElementById('last-name').value);
        formData.append('email', document.getElementById('email').value);
        formData.append('phone', document.getElementById('phone').value);
        formData.append('education', document.getElementById('education').value);
        formData.append('interest', document.getElementById('interest').value);
        formData.append('message', document.getElementById('message').value);
        
        // Validate required fields
        const requiredFields = [
            { id: 'first-name', name: 'First Name' },
            { id: 'last-name', name: 'Last Name' },
            { id: 'email', name: 'Email' },
            { id: 'education', name: 'Education/Position' },
            { id: 'interest', name: 'Area of Interest' },
            { id: 'message', name: 'Message' }
        ];
        
        for (const field of requiredFields) {
            const element = document.getElementById(field.id);
            if (!element.value.trim()) {
                showMessage(`${field.name} is required`, 'error');
                element.focus();
                return;
            }
        }
        
        // Validate email format
        const email = document.getElementById('email').value;
        if (!isValidEmail(email)) {
            showMessage('Please enter a valid email address', 'error');
            document.getElementById('email').focus();
            return;
        }
        
        // Show loading state
        const originalButtonText = actualSubmitButton.textContent;
        actualSubmitButton.textContent = 'Submitting...';
        actualSubmitButton.disabled = true;
        
        // Submit form
        fetch('/submit-application', {
            method: 'POST',
            body: formData
        })
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
=======
        .then(response => response.json())
>>>>>>> Stashed changes
=======
        .then(response => response.json())
>>>>>>> Stashed changes
=======
        .then(response => response.json())
>>>>>>> Stashed changes
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                form.reset();
            } else {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                showMessage(data.message || 'Failed to submit application. Please try again.', 'error');
=======
                showMessage(data.message, 'error');
>>>>>>> Stashed changes
=======
                showMessage(data.message, 'error');
>>>>>>> Stashed changes
=======
                showMessage(data.message, 'error');
>>>>>>> Stashed changes
            }
        })
        .catch(error => {
            console.error('Error:', error);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            const errorMessage = error.message || 'An error occurred. Please try again.';
            showMessage(errorMessage, 'error');
=======
            showMessage('An error occurred. Please try again.', 'error');
>>>>>>> Stashed changes
=======
            showMessage('An error occurred. Please try again.', 'error');
>>>>>>> Stashed changes
=======
            showMessage('An error occurred. Please try again.', 'error');
>>>>>>> Stashed changes
        })
        .finally(() => {
            // Reset button state
            actualSubmitButton.textContent = originalButtonText;
            actualSubmitButton.disabled = false;
        });
    }
    
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    function showMessage(message, type) {
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
});