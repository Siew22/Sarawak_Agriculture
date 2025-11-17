// ====================================================================
//  frontend/auth.js (Final Two-Page Version)
// ====================================================================

// ====================================================================
//  Configuration
// ====================================================================
const API_BASE_URL = 'https://juliette-unattempted-tammara.ngrok-free.dev';
const USERS_API_URL = `${API_BASE_URL}/users/`;
const TOKEN_API_URL = `${API_BASE_URL}/token`;

// ====================================================================
//  DOM Element Selection
// ====================================================================
const loginView = document.getElementById('loginView');
const choiceView = document.getElementById('choiceView');
const signUpView = document.getElementById('signUpView');
const showSignUpLink = document.getElementById('showSignUpLink');
const showLoginLinkFromChoice = document.getElementById('showLoginLinkFromChoice');
const showLoginLinkFromSignUp = document.getElementById('showLoginLinkFromSignUp');
const choiceBusiness = document.getElementById('choiceBusiness');
const choicePublic = document.getElementById('choicePublic');
const signUpForm = document.getElementById('signUpForm');
const loginForm = document.getElementById('loginForm');
const signUpTitle = document.getElementById('signUpTitle');
const userTypeInput = document.getElementById('userType');
const businessFields = document.getElementById('businessFields');
const signUpIcNo = document.getElementById('signUpIcNo');
const signUpError = document.getElementById('signUpError');
const loginError = document.getElementById('loginError');

// ====================================================================
//  Navigation Logic
// ====================================================================
function showView(viewToShow) {
    // Hide all sibling views
    const views = document.querySelectorAll('.view');
    views.forEach(view => {
        if (view) view.classList.remove('active');
    });
    // Show the target view
    if (viewToShow) {
        viewToShow.classList.add('active');
    }
}

if (showSignUpLink) {
    showSignUpLink.addEventListener('click', (e) => { e.preventDefault(); showView(choiceView); });
}
if (showLoginLinkFromChoice) {
    showLoginLinkFromChoice.addEventListener('click', (e) => { e.preventDefault(); showView(loginView); });
}
if (showLoginLinkFromSignUp) {
    showLoginLinkFromSignUp.addEventListener('click', (e) => { e.preventDefault(); showView(loginView); });
}
if (choicePublic) {
    choicePublic.addEventListener('click', () => {
        signUpTitle.textContent = 'Create Public Account';
        userTypeInput.value = 'public';
        businessFields.classList.add('hidden');
        signUpIcNo.placeholder = "IC-No.";
        const signUpOrg = document.getElementById('signUpOrg');
        if(signUpOrg) signUpOrg.value = '';
        showView(signUpView);
    });
}
if (choiceBusiness) {
    choiceBusiness.addEventListener('click', () => {
        signUpTitle.textContent = 'Create Business Account';
        userTypeInput.value = 'business';
        businessFields.classList.remove('hidden');
        signUpIcNo.placeholder = "IC / Business Registration No.";
        showView(signUpView);
    });
}

// ====================================================================
//  Form Submission & API Logic
// ====================================================================
if (signUpForm) {
    signUpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        signUpError.textContent = 'Processing...';

        const password = document.getElementById('signUpPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        if (password !== confirmPassword) {
            signUpError.textContent = 'Passwords do not match!';
            return;
        }

        const user_type = userTypeInput.value;
        const signUpOrg = document.getElementById('signUpOrg');
        const formData = {
            email: document.getElementById('signUpEmail').value,
            password: password,
            user_type: user_type,
            name: document.getElementById('signUpName').value,
            ic_no: signUpIcNo.value || null,
            phone_number: document.getElementById('signUpPhone').value || null,
            organization: user_type === 'business' && signUpOrg ? signUpOrg.value || null : null,
            company_type: user_type === 'business' ? (document.querySelector('input[name="companyType"]:checked') ? document.querySelector('input[name="companyType"]:checked').value : null) : null,
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
            showView(null);
            createVerificationView(data.user_id, formData.email);
        } catch (error) {
            signUpError.textContent = error.message;
        }
    });
}


function createVerificationView(userId, email) {
    const oldView = document.getElementById('verificationView');
    if(oldView) oldView.remove();
    
    const verificationBox = document.createElement('div');
    verificationBox.className = 'auth-box';
    verificationBox.innerHTML = `
        <h2>Verify Your Email</h2>
        <p>A 6-digit code has been sent. Check your Docker logs for the 'mail' service to get the code.</p>
        <form id="verifyForm">
            <input type="text" id="verificationCode" placeholder="Enter 6-digit code" required maxlength="6" pattern="[0-9]{6}">
            <button type="submit" class="glow-button">Verify Account</button>
        </form>
        <p id="verifyError" class="error-message"></p>
    `;
    const verificationView = document.createElement('div');
    verificationView.id = 'verificationView';
    verificationView.className = 'view auth-container active';
    verificationView.appendChild(verificationBox);
    document.body.appendChild(verificationView);

    document.getElementById('verifyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.getElementById('verificationCode').value;
        const verifyError = document.getElementById('verifyError');
        verifyError.textContent = 'Verifying...';
        try {
            const verifyUrl = `${USERS_API_URL}verify-email?user_id=${userId}&code=${code}`;
            const verifyResponse = await fetch(verifyUrl, { method: 'POST' });
            const verifyData = await verifyResponse.json();
            if (!verifyResponse.ok) {
                throw new Error(verifyData.detail || 'Verification failed.');
            }
            alert('Email verified successfully! Please log in.');
            verificationView.remove();
            showView(loginView);
        } catch (error) {
            verifyError.textContent = error.message;
        }
    });
}

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = 'Logging in...';
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const bodyString = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;

    try {
        const response = await fetch(TOKEN_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: bodyString,
        });

        // 【【【 核心修复：将所有 response 处理逻辑移入 try 块 】】】

        // 1. 检查 response.ok 状态
        if (!response.ok) {
            // 如果请求失败 (例如 400, 401, 500)，先尝试解析错误信息
            const errorData = await response.json().catch(() => {
                // 如果连 JSON 解析都失败，说明返回的不是标准的错误格式
                return { detail: `Login failed with status: ${response.status}` };
            });
            throw new Error(errorData.detail || 'Login failed.');
        }

        // 2. 如果请求成功，解析成功的 JSON 数据
        const data = await response.json();

        // 3. 执行成功后的逻辑
        localStorage.setItem('accessToken', data.access_token);
        window.location.href = './dashboard.html';

    } catch (error) {
        // 所有错误（网络错误、服务器错误）最终都会在这里被捕获
        loginError.textContent = error.message;
    }
})};