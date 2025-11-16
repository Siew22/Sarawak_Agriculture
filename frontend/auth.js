// ====================================================================
//  Configuration
// ====================================================================

// API Endpoints
const API_BASE_URL = 'https://3ab453a224d5.ngrok-free.app'; 

const USERS_API_URL = `${API_BASE_URL}/users/`;
const TOKEN_API_URL = `${API_BASE_URL}/auth/token`;

// ====================================================================
//  DOM Element Selection
// ====================================================================

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

// ====================================================================
//  Navigation Logic
// ====================================================================

/**
 * Hides all main views and shows only the specified view.
 * @param {HTMLElement} viewToShow The view container element to make active.
 */
function showView(viewToShow) {
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    if (viewToShow) {
        viewToShow.classList.add('active');
    }
}

// Event listeners for switching between Login, Choice, and SignUp views
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

// Event listeners for choosing user type (Public/Business)
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

// ====================================================================
//  Form Submission & API Logic
// ====================================================================

/**
 * Handles the submission of the Sign Up form.
 */
signUpForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    signUpError.textContent = '';

    const password = document.getElementById('signUpPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        signUpError.textContent = 'Passwords do not match!';
        return;
    }

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
        company_type: selectedCompanyType,
    };

    try {
        const response = await fetch(USERS_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Sign up failed.');
        }

        // --- Registration successful, proceed to verification step ---
        const userId = data.user_id;
        showView(null); // Hide all main views
        createVerificationView(userId, formData.email);

    } catch (error) {
        signUpError.textContent = error.message;
    }
});

/**
 * Dynamically creates and displays the email verification view.
 * @param {number} userId - The ID of the newly created user.
 * @param {string} email - The email address the code was sent to.
 */
function createVerificationView(userId, email) {
    const verificationBox = document.createElement('div');
    verificationBox.className = 'auth-box';
    verificationBox.innerHTML = `
        <h2>Verify Your Email</h2>
        <p>A 6-digit code has been sent to ${email}.</p>
        <form id="verifyForm">
            <input type="text" id="verificationCode" placeholder="Enter 6-digit code" required maxlength="6" pattern="[0-9]{6}">
            <button type="submit" class="glow-button">Verify Account</button>
        </form>
        <p id="verifyError" class="error-message"></p>
    `;

    const verificationView = document.createElement('div');
    verificationView.id = 'verificationView'; // Give it an ID for easy removal
    verificationView.className = 'view auth-container active';
    verificationView.appendChild(verificationBox);
    
    document.body.appendChild(verificationView);

    const verifyForm = document.getElementById('verifyForm');
    verifyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('verificationCode').value;
        const verifyError = document.getElementById('verifyError');
        verifyError.textContent = '';

        try {
            const verifyUrl = `${USERS_API_URL}verify-email?user_id=${userId}&code=${code}`;
            const verifyResponse = await fetch(verifyUrl, {
                method: 'POST'
            });

            const verifyData = await verifyResponse.json();

            if (!verifyResponse.ok) {
                throw new Error(verifyData.detail || 'Verification failed.');
            }
            
            alert('Email verified successfully! Please log in.');
            verificationView.remove(); // Remove the verification view
            showView(loginView); // Show the login view

        } catch (error) {
            verifyError.textContent = error.message;
        }
    });
}

/**
 * Handles the submission of the Login form.
 */
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = '';
    
    // 【【【 在这里加上我们的“铁证” 】】】
    alert(`Vercel 部署已更新！正在向 ${API_BASE_URL} 发送登录请求...`);

    const loginPayload = new FormData();
    loginPayload.append('username', document.getElementById('loginEmail').value);
    loginPayload.append('password', document.getElementById('loginPassword').value);

    try {
        const response = await fetch(TOKEN_API_URL, {
            method: 'POST',
            body: loginPayload,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed.');
        }

        localStorage.setItem('accessToken', data.access_token);
        alert('Login successful! Redirecting to dashboard...');
        
        window.location.href = './dashboard.html';

    } catch (error) {
        loginError.textContent = error.message;
    }
});