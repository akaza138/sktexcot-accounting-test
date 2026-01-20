const Utils = {
    // Toast Notification
    showToast: (message, type = 'success') => {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerText = message;
        document.body.appendChild(toast);

        // CSS for toast should be in style.css
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // Format Currency
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount || 0);
    },

    // Format Date
    formatDate: (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('en-IN');
    },

    // API Wrapper
    api: {
        async request(endpoint, method = 'GET', data = null) {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Content-Type': 'application/json'
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const config = {
                method,
                headers,
            };

            if (data) {
                config.body = JSON.stringify(data);
            }

            // Helper for safe JSON parsing
            async function safeJson(response) {
                const text = await response.text();
                if (!text) return null;
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.warn("Response was not valid JSON:", text);
                    return null;
                }
            }

            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, config);

                // Handle 401 Unauthorized (Token Expiry)
                if (response.status === 401) {
                    Auth.logout();
                    return null;
                }

                const result = await safeJson(response);

                if (!response.ok) {
                    // Use result message or fallback to status text
                    const msg = (result && (result.detail || result.message || result.error)) || `Request failed (${response.status})`;
                    throw new Error(msg);
                }

                // If result is null (empty body) but response was OK, return empty object or null
                return result;
            } catch (error) {
                Utils.showToast(error.message, 'error');
                console.error('API Request Failed:', error);
                throw error;
            }
        },

        get: (endpoint) => Utils.api.request(endpoint, 'GET'),
        post: (endpoint, data) => Utils.api.request(endpoint, 'POST', data),
        put: (endpoint, data) => Utils.api.request(endpoint, 'PUT', data),
        delete: (endpoint) => Utils.api.request(endpoint, 'DELETE'),

        // Special handler for file upload
        async upload(endpoint, formData) {
            const token = localStorage.getItem('access_token');

            // Helper for safe JSON parsing
            async function safeJson(response) {
                const text = await response.text();
                if (!text) return null;
                try {
                    return JSON.parse(text);
                } catch (e) {
                    console.warn("Response was not valid JSON:", text);
                    return null;
                }
            }

            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                        // Content-Type not set, let browser set boundary
                    },
                    body: formData
                });

                // Handle 401 Unauthorized
                if (response.status === 401) {
                    Auth.logout();
                    return null;
                }

                const result = await safeJson(response);

                if (!response.ok) {
                    const msg = (result && (result.detail || result.message || result.error)) || `Upload failed (${response.status})`;
                    throw new Error(msg);
                }

                return result;
            } catch (error) {
                Utils.showToast(error.message, 'error');
                console.error('Upload failed:', error);
                throw error;
            }
        }
    }
};