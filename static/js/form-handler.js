// Form submission handler
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitButton = document.querySelector('button[type="submit"]') || 
                        Array.from(document.querySelectorAll('button')).find(btn => 
                            btn.textContent.includes('Submit'));

    if (!form || !submitButton) return;

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitForm();
    });

    function submitForm() {
        // Prevent page navigation
        window.history.pushState(null, null, window.location.href);
        window.addEventListener('popstate', function(event) {
            window.history.pushState(null, null, window.location.href);
        });

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

        // Check required fields
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
        const originalButtonText = submitButton.textContent;
        submitButton.textContent = 'Submitting...';
        submitButton.disabled = true;
        submitButton.style.backgroundColor = '#4f46e5';
        submitButton.style.color = 'white';

        // Submit form
        fetch('/submit-application', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Show success message and reset form
                showMessage(data.message, 'success');
                form.reset();
                
                // Animate submit button
                submitButton.textContent = '✓ Application Sent!';
                submitButton.style.backgroundColor = '#10b981';
                
                // Reset button after 3 seconds
                setTimeout(() => {
                    submitButton.textContent = originalButtonText;
                    submitButton.style.backgroundColor = '';
                    submitButton.style.color = '';
                }, 3000);
            } else {
                // Handle error
                showMessage(data.message || 'Failed to submit application. Please try again.', 'error');
                submitButton.style.backgroundColor = '#ef4444';
                
                // Reset button after 1 second
                setTimeout(() => {
                    submitButton.style.backgroundColor = '';
                    submitButton.style.color = '';
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = error.message || 'An error occurred. Please try again.';
            showMessage(errorMessage, 'error');
            submitButton.style.backgroundColor = '#ef4444';
            
            // Reset button after 1 second
            setTimeout(() => {
                submitButton.style.backgroundColor = '';
                submitButton.style.color = '';
            }, 1000);
        })
        .finally(() => {
            // Reset button state
            submitButton.textContent = originalButtonText;
            submitButton.disabled = false;
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