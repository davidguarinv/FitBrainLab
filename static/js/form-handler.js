// Enhanced Form submission handler with proper URL handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('Form handler initialized');

    // Main form submission handler
    function handleFormSubmission(form, url) {
        console.log(`Setting up handler for form with URL: ${url}`);
        
        form.addEventListener('submit', async function(e) {
            console.log(`Form submitted to: ${url}`);
            e.preventDefault();
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = 'Submitting...';
            
            // Get form data
            const formData = new FormData(this);
            
            // Log form data for debugging
            console.log('Form data being sent:');
            for (let [key, value] of formData.entries()) {
                console.log(`${key}: ${value}`);
            }
            
            try {
                console.log(`Sending POST request to: ${url}`);
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                console.log(`Response status: ${response.status}`);
                console.log(`Response headers:`, response.headers);
                
                if (!response.ok) {
                    // Try to get error message from response
                    let errorMessage = `Server error (${response.status})`;
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.message || errorMessage;
                    } catch (jsonError) {
                        // If response isn't JSON, try to get text
                        try {
                            const errorText = await response.text();
                            if (errorText.includes('Not Found')) {
                                errorMessage = `Route not found. Please check the URL: ${url}`;
                            } else {
                                errorMessage = errorText.substring(0, 100) + '...';
                            }
                        } catch (textError) {
                            console.error('Could not parse error response:', textError);
                        }
                    }
                    throw new Error(errorMessage);
                }

                const result = await response.json();
                console.log('Server response:', result);
                
                if (result.success) {
                    // Show success message
                    console.log('Showing success message');
                    showMessage(result.message, 'success', form);
                    // Clear the form
                    this.reset();
                } else {
                    // Show error message
                    console.log('Showing error message');
                    showMessage(result.message || 'Failed to submit form. Please try again.', 'error', form);
                }
            } catch (error) {
                console.error('Error submitting form:', error);
                showMessage(`Error: ${error.message}`, 'error', form);
            } finally {
                // Restore button state
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }

    // Find and handle forms with data-url attribute
    const formsWithDataUrl = document.querySelectorAll('form[data-url]');
    console.log(`Found ${formsWithDataUrl.length} forms with data-url attribute`);
    
    formsWithDataUrl.forEach((form, index) => {
        const url = form.dataset.url;
        if (url) {
            console.log(`Form ${index + 1}: Setting up handler for URL: ${url}`);
            handleFormSubmission(form, url);
        } else {
            console.error(`Form ${index + 1}: Found form with data-url attribute but URL is empty`);
        }
    });

    // Handle specific forms by action attribute (fallback method)
    const specificForms = [
        { selector: 'form[action="/submit-application"]', url: '/submit-application' },
        { selector: 'form[action*="submit_community"]', url: '/submit_community' },
        { selector: 'form[method="POST"]:not([data-url])', url: null } // Generic POST forms
    ];

    specificForms.forEach(formConfig => {
        const forms = document.querySelectorAll(formConfig.selector);
        forms.forEach((form, index) => {
            // Skip if already handled by data-url
            if (form.hasAttribute('data-url')) {
                return;
            }
            
            let url = formConfig.url;
            
            // If no predefined URL, try to get from action attribute
            if (!url) {
                url = form.getAttribute('action');
                if (!url || url === '#' || url === '') {
                    console.warn(`Form found but no valid URL available:`, form);
                    return;
                }
            }
            
            console.log(`Fallback handler: Setting up form ${index + 1} with URL: ${url}`);
            handleFormSubmission(form, url);
        });
    });

    // Helper function to validate URLs
    function isValidUrl(url) {
        try {
            // Check if it's a relative URL (starts with /)
            if (url.startsWith('/')) {
                return true;
            }
            // Check if it's a full URL
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Helper function to normalize URLs
    function normalizeUrl(url) {
        // Ensure URL starts with / for relative URLs
        if (!url.startsWith('/') && !url.includes('://')) {
            url = '/' + url;
        }
        return url;
    }

    // Enhanced message display function
    function showMessage(message, type, form) {
        console.log(`Showing ${type} message: ${message}`);
        
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.form-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `form-message p-4 rounded-md mb-4 ${
            type === 'success' 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
        }`;
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '&times;';
        closeButton.className = 'float-right text-xl font-bold cursor-pointer hover:opacity-70';
        closeButton.onclick = () => messageDiv.remove();
        
        const messageText = document.createElement('div');
        messageText.textContent = message;
        
        messageDiv.appendChild(closeButton);
        messageDiv.appendChild(messageText);
        
        // Insert message in the best location
        let insertLocation = form;
        
        // Try to find a better container (like a form wrapper)
        const formContainer = form.closest('.container, .max-w-xl, section');
        if (formContainer) {
            insertLocation = formContainer;
        }
        
        // Insert message before the form or container
        if (insertLocation && insertLocation.parentNode) {
            insertLocation.parentNode.insertBefore(messageDiv, insertLocation);
            
            // Auto-remove success messages after 8 seconds
            if (type === 'success') {
                setTimeout(() => {
                    if (messageDiv.parentNode) {
                        messageDiv.style.transition = 'opacity 0.5s';
                        messageDiv.style.opacity = '0';
                        setTimeout(() => messageDiv.remove(), 500);
                    }
                }, 8000);
            }
            
            // Scroll to message smoothly
            messageDiv.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest',
                inline: 'nearest'
            });
        } else {
            console.error('Could not find suitable location to insert message');
        }
    }

    // Email validation helper
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Debug function to check current page forms
    function debugForms() {
        console.log('=== FORM DEBUG INFO ===');
        const allForms = document.querySelectorAll('form');
        console.log(`Total forms found: ${allForms.length}`);
        
        allForms.forEach((form, index) => {
            console.log(`Form ${index + 1}:`);
            console.log(`  - Action: ${form.getAttribute('action') || 'not set'}`);
            console.log(`  - Method: ${form.getAttribute('method') || 'GET'}`);
            console.log(`  - Data-URL: ${form.getAttribute('data-url') || 'not set'}`);
            console.log(`  - ID: ${form.id || 'not set'}`);
            console.log(`  - Classes: ${form.className || 'not set'}`);
        });
        console.log('=== END FORM DEBUG ===');
    }

    // Run debug in development (you can remove this in production)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        debugForms();
    }

    console.log('Form handler setup complete');
});