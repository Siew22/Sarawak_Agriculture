// ====================================================================
//  frontend/dashboard.js (Final & Complete Version - Professionally Formatted)
// ====================================================================

// --- 1. Configuration & Global State ---
const API_BASE_URL = 'http://127.0.0.1:8000';
const USERS_ME_API_URL = `${API_BASE_URL}/users/me`;
const DIAGNOSE_API_URL = `${API_BASE_URL}/diagnose`;
const DIAGNOSES_HISTORY_API_URL = `${API_BASE_URL}/diagnoses/me`;
const POSTS_API_URL = `${API_BASE_URL}/posts/`;
const PRODUCTS_API_URL = `${API_BASE_URL}/products/`;
const SUBSCRIPTION_API_URL = `${API_BASE_URL}/users/me/subscription`;

const appContainer = document.getElementById('app-container');
let currentUser = null;
const accessToken = localStorage.getItem('accessToken');

// --- 2. Core API Fetch Helper ---
async function apiFetch(url, options = {}) {
    const defaultHeaders = {
        'Authorization': `Bearer ${accessToken}`
    };
    if (!(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    const config = {
        ...options,
        headers: { ...defaultHeaders, ...options.headers },
        cache: 'no-cache', // Force browser to always revalidate with the server
    };

    const response = await fetch(url, config);
    const contentType = response.headers.get("content-type");

    if (!response.ok) {
        let errorData = { detail: `HTTP error! status: ${response.status}` };
        if (contentType && contentType.indexOf("application/json") !== -1) {
            errorData = await response.json();
        }
        throw new Error(errorData.detail);
    }
    if (response.status === 204 || !contentType || !contentType.includes("application/json")) {
        return null;
    }
    return response.json();
}

// --- 3. Initialization on Page Load ---
document.addEventListener('DOMContentLoaded', async () => {
    if (!accessToken) {
        window.location.href = 'login.html';
        return;
    }
    try {
        currentUser = await apiFetch(USERS_ME_API_URL);
        renderDashboard();
    } catch (e) {
        console.error("Session is invalid or expired:", e);
        logout();
    }
});

// --- 4. Core Rendering Functions ---

function renderDashboard() {
    appContainer.innerHTML = '';
    const dashboardContainer = document.createElement('div');
    dashboardContainer.className = 'dashboard-container';
    
    const header = document.createElement('header');
    const { permissions, user_type, email } = currentUser;
    
    let navLinks = `
        <a href="#" class="nav-link" data-view="profile">Profile</a>
        <a href="#" class="nav-link active-link" data-view="ai-diagnosis">AI Diagnosis</a>
        <a href="#" class="nav-link" data-view="diagnosis-history">History</a>
        <a href="#" class="nav-link ${!permissions.can_post ? 'disabled-link' : ''}" data-view="posts">Posts</a>
        <a href="#" class="nav-link ${!permissions.can_chat ? 'disabled-link' : ''}" data-view="chat">Chat</a>
        <a href="#" class="nav-link ${!permissions.can_shop ? 'disabled-link' : ''}" data-view="shopping">Shopping</a>
    `;
    if (user_type === 'business') {
        navLinks += `<a href="#" class="nav-link" data-view="business-profile">Business Profile</a>`;
    }

    header.innerHTML = `
        <div class="logo">Sarawak <span>Agri-Advisor</span></div>
        <nav>${navLinks}</nav>
        <div>
            <span id="welcomeUser">Welcome, ${email}</span>
            <button id="logoutButton" class="nav-button">Logout</button>
        </div>
    `;
    dashboardContainer.appendChild(header);

    const main = document.createElement('main');
    main.id = 'mainContent';
    dashboardContainer.appendChild(main);
    appContainer.appendChild(dashboardContainer);
    
    attachNavListeners();
    document.getElementById('logoutButton').addEventListener('click', logout);

    const urlParams = new URLSearchParams(window.location.search);
    const view = urlParams.get('view');
    renderView(view || 'ai-diagnosis');
}

async function renderView(viewId) {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = `<div class="card full-width" style="text-align: center;"><div class="spinner"></div></div>`;

    document.querySelectorAll('nav a, nav button').forEach(link => {
        link.classList.remove('active-link');
        if (link.dataset.view === viewId) {
            link.classList.add('active-link');
        }
    });
    
    try {
        if (viewId === 'ai-diagnosis') {
            mainContent.innerHTML = getAIDiagnosisHTML();
            attachDiagnosisListeners();
        } else if (viewId === 'diagnosis-history') {
            const history = await apiFetch(DIAGNOSES_HISTORY_API_URL);
            mainContent.innerHTML = getDiagnosisHistoryHTML(history);
        } else if (viewId === 'posts') {
            mainContent.innerHTML = getPostsHTML([]);
        } else if (viewId === 'shopping') {
            mainContent.innerHTML = getShoppingHTML([]);
        } else if (viewId === 'business-profile' && currentUser.user_type === 'business') {
            mainContent.innerHTML = getBusinessProfileHTML();
        } else if (viewId === 'profile') {
            const latestUser = await apiFetch(USERS_ME_API_URL);
            currentUser = latestUser;
            mainContent.innerHTML = getProfileHTML(currentUser);
            attachPlanButtonListeners();
        } else {
            const capitalizedViewId = viewId.charAt(0).toUpperCase() + viewId.slice(1);
            mainContent.innerHTML = `<div class="card full-width"><h3>${capitalizedViewId}</h3><p>Content for this view is coming soon.</p></div>`;
        }
    } catch (error) {
        mainContent.innerHTML = `<div class="card full-width error-message"><p>Failed to load view: ${error.message}</p></div>`;
    }
}

// --- 5. HTML Template Generators ---

function getAIDiagnosisHTML() {
    return `
        <div class="card full-width">
            <h3>AI Diagnosis</h3>
            <div class="input-group" style="margin-bottom: 20px; max-width: 300px;">
                <label for="languageSelect" style="display: block; margin-bottom: 5px; color: var(--text-secondary);">Report Language:</label>
                <select id="languageSelect">
                    <option value="en">English</option>
                    <option value="ms">Bahasa Malaysia</option>
                    <option value="zh">Chinese (简体中文)</option>
                </select>
            </div>
            <label for="imageUpload" class="diagnosis-uploader">
                <p>Click here to upload a leaf photo for analysis</p>
                <img id="imagePreview" src="" alt="Image preview" hidden>
            </label>
            <input type="file" id="imageUpload" accept="image/*">
            <div id="loadingIndicator" class="hidden">
                <div class="spinner"></div>
                <p>Analyzing... This may take a moment.</p>
            </div>
            <div id="reportContainer"></div>
        </div>
    `;
}

function getDiagnosisHistoryHTML(history) {
    if (!history || history.length === 0) {
        return `
            <div class="card full-width">
                <h3>Diagnosis History</h3>
                <p>No diagnosis history found. Perform a diagnosis to see your history here.</p>
            </div>
        `;
    }
    const historyCards = history.map(item => `
        <div class="card">
            <img src="${API_BASE_URL}${item.image_url}" style="width:100%; border-radius:8px; margin-bottom: 15px;">
            <h4>${item.report_title}</h4>
            <p><strong>Result:</strong> ${item.disease_name} (${(item.confidence * 100).toFixed(2)}%)</p>
            <p style="font-size: 0.9em; color: var(--text-secondary);">
                <strong>Date:</strong> ${new Date(item.timestamp).toLocaleString()}
            </p>
        </div>
    `).join('');
    return `<div class="view-content">${historyCards}</div>`;
}

function getPostsHTML(posts) {
    let html = `<h3>Community Posts</h3>`;
    if (currentUser.permissions.can_post) {
        html += `
            <form id="createPostForm" style="margin-bottom: 20px;">
                <textarea name="content" placeholder="What's on your mind?" required style="width: 100%; min-height: 80px;"></textarea>
                <button type="submit" class="glow-button">Post</button>
            </form>
        `;
    }
    html += `<p>Coming Soon.</p>`;
    return `<div class="card full-width">${html}</div>`;
}

function getShoppingHTML(products) {
    return `<div class="card full-width"><h3>Marketplace</h3><p>Coming Soon.</p></div>`;
}

function getBusinessProfileHTML() {
    return `
        <div class="view-content">
            <div class="card">
                <h3>Income</h3>
                <p>Coming Soon.</p>
            </div>
            <div class="card">
                <h3>Product Sell Quantity</h3>
                <p>Coming Soon.</p>
            </div>
            <div class="card">
                <h3>Add Product</h3>
                <p>Coming Soon.</p>
            </div>
        </div>
    `;
}

function getProfileHTML(user) {
    const tier = user.subscription_tier || 'free';
    let planName = 'Free Tier';
    if (tier === 'tier_10') planName = 'Pro (RM10)';
    else if (tier === 'tier_15') planName = 'Pro Plus (RM15)';
    else if (tier === 'tier_20') planName = 'Business Pro (RM20)';
    let planButtonsHTML = '';
    if (user.user_type === 'public') {
        if (tier !== 'tier_10') {
            planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_10">Subscribe to RM10 Plan</button>`;
        }
        if (tier !== 'tier_15') {
            const buttonText = (tier === 'tier_10') ? 'Upgrade to RM15 Plan' : 'Subscribe to RM15 Plan';
            planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_15">${buttonText}</button>`;
        }
    }
    if (user.user_type === 'business' && tier !== 'tier_20') {
        planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_20">Subscribe to RM20 Business Plan</button>`;
    }
    if (tier !== 'free') {
        planButtonsHTML += `<button class="plan-btn-secondary plan-btn" data-plan="free">Downgrade to Free Tier</button>`;
    }
    return `
        <div class="card full-width">
            <h3>My Profile</h3>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>User Type:</strong> ${user.user_type}</p>
            <p><strong>Current Plan:</strong> ${planName}</p>
            <h4 style="margin-top: 30px;">Change Plan</h4>
            <div class="plans" style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">
                ${planButtonsHTML}
            </div>
            <p id="payment-error" class="error-message"></p>
        </div>
    `;
}

function renderReport(data) {
    const reportContainer = document.getElementById('reportContainer');
    let xaiImageHTML = '';
    if (data.xai_image_url) {
        xaiImageHTML = `
            <div class="report-section">
                <h4>Model Attention (XAI)</h4>
                <p>The highlighted areas are what the AI focused on.</p>
                <img id="xaiImage" src="${API_BASE_URL}${data.xai_image_url}" alt="XAI Heatmap">
            </div>
        `;
    }
    reportContainer.innerHTML = `
        <div class="report-section"><h3>${data.title}</h3></div>
        <div class="report-section"><h4>Diagnosis Summary</h4><p>${data.diagnosis_summary}</p></div>
        <div class="report-section"><h4>Environmental Context</h4><p>${data.environmental_context}</p></div>
        ${xaiImageHTML}
        <div class="report-section"><h4>Management Suggestions</h4><div id="reportSuggestion">${data.management_suggestion.replace(/\n/g, '<br>')}</div></div>
    `;
}

// --- 6. Event Listeners & Interaction Logic ---

function attachNavListeners() {
    document.querySelectorAll('nav a, nav button').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.currentTarget.classList.contains('disabled-link')) {
                alert('This feature is not available for your current subscription plan.');
                return;
            }
            const viewId = e.currentTarget.dataset.view;
            renderView(viewId);
        });
    });
}

function attachDiagnosisListeners() {
    const imageUpload = document.getElementById('imageUpload');
    imageUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('imagePreview').src = e.target.result;
                document.getElementById('imagePreview').hidden = false;
                getGPSAndDiagnose(file);
            };
            reader.readAsDataURL(file);
        }
    });
}

async function getGPSAndDiagnose(file) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const reportContainer = document.getElementById('reportContainer');
    loadingIndicator.classList.remove('hidden');
    reportContainer.innerHTML = '';
    
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            const selectedLanguage = document.getElementById('languageSelect').value;
            const formData = new FormData();
            formData.append("image", file);
            formData.append("latitude", latitude);
            formData.append("longitude", longitude);
            formData.append("language", selectedLanguage);
            try {
                const data = await apiFetch(DIAGNOSE_API_URL, { method: 'POST', body: formData });
                renderReport(data);
            } catch (error) {
                reportContainer.innerHTML = `<p class="error-message">${error.message}</p>`;
            } finally {
                loadingIndicator.classList.add('hidden');
            }
        },
        () => {
            alert("Unable to retrieve your location.");
            loadingIndicator.classList.add('hidden');
        }
    );
}

function attachPlanButtonListeners() {
    document.querySelectorAll('.plan-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            if (e.target.disabled) return;
            const plan = e.target.dataset.plan;
            const errorP = document.getElementById('payment-error');
            errorP.textContent = '';
            const planDisplayName = plan === 'free' ? 'Free Tier' : plan.replace('tier_', 'RM ');
            if (!confirm(`Are you sure you want to switch to the ${planDisplayName} plan?`)) {
                return;
            }
            try {
                const updatedUser = await apiFetch(SUBSCRIPTION_API_URL, {
                    method: 'PUT',
                    body: JSON.stringify({ plan: plan }),
                });
                currentUser = updatedUser;
                alert('Plan updated successfully!');
                renderView('profile');
            } catch (error) {
                errorP.textContent = `Failed to update plan: ${error.message}`;
            }
        });
    });
}

function logout() {
    localStorage.removeItem('accessToken');
    window.location.href = 'login.html';
}