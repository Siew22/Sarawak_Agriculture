document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        // If no token, redirect to login page
        window.location.href = 'login.html';
        return;
    }

    // --- Mock User Data (later we'll fetch this from the backend) ---
    // We'll decode the JWT token to get user info in the future
    const mockUser = {
        email: 'user@example.com',
        user_type: 'business' // Change to 'public' to test public view
    };
    
    // --- DOM Elements ---
    const welcomeUser = document.getElementById('welcomeUser');
    const logoutButton = document.getElementById('logoutButton');
    const businessProfileBtn = document.getElementById('businessProfileBtn');
    const navLinks = document.querySelectorAll('.nav-link, .nav-button');
    const views = document.querySelectorAll('.view-content');

    // --- Initialization ---
    function initializeDashboard() {
        welcomeUser.textContent = `Welcome, ${mockUser.email}`;

        // Show/hide business profile button based on user type
        if (mockUser.user_type === 'business') {
            businessProfileBtn.classList.remove('hidden');
        } else {
            businessProfileBtn.classList.add('hidden');
        }

        // Set default view
        switchView('ai-diagnosis');
    }

    // --- Navigation Logic ---
    function switchView(viewId) {
        views.forEach(view => view.classList.add('hidden'));
        const activeView = document.getElementById(`${viewId}-view`);
        if (activeView) {
            activeView.classList.remove('hidden');
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = e.currentTarget.dataset.view;
            switchView(viewId);
        });
    });

    // --- Logout Logic ---
    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        window.location.href = 'login.html';
    });

    initializeDashboard();
});