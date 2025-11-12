// API Endpoints
const SIGNUP_API_URL = 'http://127.0.0.1:8000/users/';
const LOGIN_API_URL = 'http://127.0.0.1:8000/token';

// --- DOM Elements ---

// View Containers
const loginView = document.getElementById('loginView');
const choiceView = document.getElementById('choiceView');
const signUpView = document.getElementById('signUpView');

// Links & Buttons for navigation
const showSignUpLink = document.getElementById('showSignUpLink');
const showLoginLinkFromChoice = document.getElementById('showLoginLinkFromChoice');
const showLoginLinkFromSignUp = document.getElementById('showLoginLinkFromSignUp');
const choiceBusiness = document.getElementById('choiceBusiness');
const choicePublic = document.getElementById('choicePublic');

// Forms & Form Fields
const signUpForm = document.getElementById('signUpForm');
const loginForm = document.getElementById('loginForm');
const signUpTitle = document.getElementById('signUpTitle');
const userTypeInput = document.getElementById('userType');
const businessFields = document.getElementById('businessFields');
const signUpIcNo = document.getElementById('signUpIcNo');

// Error Message Paragraphs
const signUpError = document.getElementById('signUpError');
const loginError = document.getElementById('loginError');

// --- Navigation Logic ---

/**
 * Hides all views and shows only the specified view.
 * @param {HTMLElement} viewToShow The view container element to make active.
 */
function showView(viewToShow) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    viewToShow.classList.add('active');
}

// Event listeners for switching between views
showSignUpLink.addEventListener('click', (e) => {
    e.preventDefault();
    showView(choiceView);
});

showLoginLinkFromChoice.addEventListener('click', (e) => {
    e.preventDefault();
    showView(loginView);
});

showLoginLinkFromSignUp.addEventListener('click', (e) => {
    e.preventDefault();
    showView(loginView);
});

// Event listeners for choosing user type
choicePublic.addEventListener('click', () => {
    signUpTitle.textContent = 'Create Public Account';
    userTypeInput.value = 'public';
    businessFields.classList.add('hidden');
    signUpIcNo.placeholder = "IC-No.";
    showView(signUpView);
});

choiceBusiness.addEventListener('click', () => {
    signUpTitle.textContent = 'Create Business Account';
    userTypeInput.value = 'business';
    businessFields.classList.remove('hidden');
    signUpIcNo.placeholder = "IC / Business Registration No.";
    showView(signUpView);
});


// --- Form Submission Logic ---

// Sign Up Form Handler
signUpForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    signUpError.textContent = ''; // Clear previous errors
    
    const password = document.getElementById('signUpPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        signUpError.textContent = 'Passwords do not match!';
        return;
    }

    // Get the value from the checked radio button for companyType
    const selectedCompanyType = document.querySelector('input[name="companyType"]:checked') 
                                ? document.querySelector('input[name="companyType"]:checked').value 
                                : null;

    const formData = {
        email: document.getElementById('signUpEmail').value,
        password: password,
        user_type: userTypeInput.value,
        name: document.getElementById('signUpName').value,
        ic_no: signUpIcNo.value || null,
        phone_number: document.getElementById('signUpPhone').value || null,
        company_type: selectedCompanyType, // Use the value from the radio button
    };

    try {
        const response = await fetch(SIGNUP_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Sign up failed due to a server error.');
        }

        alert('Sign up successful! Please log in.');
        showView(loginView); // Switch back to login view on success

    } catch (error) {
        signUpError.textContent = error.message;
    }
});

// Login Form Handler
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = ''; // Clear previous errors
    
    const loginPayload = new FormData();
    loginPayload.append('username', document.getElementById('loginEmail').value);
    loginPayload.append('password', document.getElementById('loginPassword').value);

    try {
        const response = await fetch(LOGIN_API_URL, {
            method: 'POST',
            body: loginPayload,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed.');
        }

        const data = await response.json();

        localStorage.setItem('accessToken', data.access_token);
        alert('Login successful! Redirecting to dashboard...');
        
        window.location.href = './dashboard.html';

    } catch (error) {
        loginError.textContent = error.message;
    }
});