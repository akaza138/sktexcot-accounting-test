const Auth = {
    login: async (email, password) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINTS.LOGIN}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            // Get User Profile
            await Auth.getProfile();

            // Redirect to dashboard
            window.location.href = '/sktexcot/dashboard.html';

        } catch (error) {
            Utils.showToast(error.message, 'error');
            console.error('Login error:', error);
        }
    },

    getProfile: async () => {
        try {
            const user = await Utils.api.get(CONFIG.ENDPOINTS.ME);
            localStorage.setItem('user_role', user.role);
            localStorage.setItem('user_name', user.full_name);
            return user;
        } catch (e) {
            return null;
        }
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_name');
        window.location.href = '/sktexcot/login.html';
    },

    checkAuth: () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/sktexcot/login.html';
        } else {
            Auth.startSessionTimer();
        }
    },

    // Session Management
    sessionTimeout: 30 * 60 * 1000, // 30 minutes
    logoutTimer: null,

    startSessionTimer: () => {
        // Clear existing events to avoid duplicates if called multiple times (though checkAuth usually once)
        ['mousemove', 'mousedown', 'keypress', 'touchmove', 'scroll', 'click'].forEach(evt => {
            document.removeEventListener(evt, Auth.resetSessionTimer);
            document.addEventListener(evt, Auth.resetSessionTimer);
        });

        Auth.resetSessionTimer();
    },

    resetSessionTimer: () => {
        if (Auth.logoutTimer) clearTimeout(Auth.logoutTimer);
        Auth.logoutTimer = setTimeout(() => {
            alert('Session expired due to inactivity.');
            Auth.logout();
        }, Auth.sessionTimeout);
    }
};
