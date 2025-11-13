// ====================================================================
//  frontend/dashboard.js (Final & Complete Version)
// ====================================================================
const API_BASE_URL = 'http://127.0.0.1:8000';
const DIAGNOSE_API_URL = `${API_BASE_URL}/diagnose`;
const appContainer = document.getElementById('app-container');
let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    const accessToken = localStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = 'login.html';
        return;
    }
    try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        if (payload.exp * 1000 < Date.now()) {
            throw new Error("Token expired");
        }
        currentUser = { id: payload.id, email: payload.sub, type: payload.type };
        renderDashboard();
    } catch (e) {
        console.error("Token is invalid or expired:", e);
        localStorage.removeItem('accessToken');
        window.location.href = 'login.html';
    }
});

function renderDashboard() {
    appContainer.innerHTML = '';
    const dashboardContainer = document.createElement('div');
    dashboardContainer.className = 'dashboard-container';
    const header = document.createElement('header');
    let navLinks = `
        <a href="#" class="nav-link active-link" data-view="ai-diagnosis">AI Diagnosis</a>
        <a href="#" class="nav-link" data-view="posts">Posts</a>
        <a href="#" class="nav-link" data-view="chat">Chat</a>
        <a href="#" class="nav-link" data-view="shopping">Shopping</a>
    `;
    if (currentUser.type === 'business') {
        navLinks += `<a href="#" class="nav-link" data-view="business-profile">Business Profile</a>`;
    }
    header.innerHTML = `
        <div class="logo">Sarawak <span>Agri-Advisor</span></div>
        <nav>${navLinks}</nav>
        <div>
            <span id="welcomeUser">Welcome, ${currentUser.email}</span>
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
    renderView('ai-diagnosis');
}

function renderView(viewId) {
    const mainContent = document.getElementById('mainContent');
    mainContent.innerHTML = '';
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active-link');
        if (link.dataset.view === viewId) {
            link.classList.add('active-link');
        }
    });
    if (viewId === 'ai-diagnosis') {
        mainContent.innerHTML = getAIDiagnosisHTML();
        attachDiagnosisListeners();
    } else if (viewId === 'business-profile' && currentUser.type === 'business') {
        mainContent.innerHTML = getBusinessProfileHTML();
    } else {
        const capitalizedViewId = viewId.charAt(0).toUpperCase() + viewId.slice(1);
        mainContent.innerHTML = `<div class="card full-width"><h3>${capitalizedViewId}</h3><p>Content for ${viewId} will go here.</p></div>`;
    }
}

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
            <div id="loadingIndicator" class="hidden"><div class="spinner"></div><p>Analyzing... This may take a moment.</p></div>
            <div id="reportContainer"></div>
        </div>
    `;
}

function getBusinessProfileHTML() {
    return `
        <div class="card"><h3>Income</h3><p>Data visualization for income will be displayed here.</p></div>
        <div class="card"><h3>Product Sell Quantity</h3><p>Data visualization for sales will be displayed here.</p></div>
        <div class="card">
            <h3>Add Product to Sell</h3>
            <form id="addProductForm">
                <input type="text" placeholder="Product Name" required>
                <input type="text" placeholder="Description">
                <input type="text" placeholder="Location">
                <input type="number" placeholder="Price (RM)" step="0.01" required>
                <label class="file-input-label">Product Picture <input type="file" class="file-input"></label>
                <button type="submit" class="glow-button">Add Product</button>
            </form>
        </div>
        <div class="card full-width"><h3>Business User Profile Details</h3><p>Editable profile information will be displayed here.</p></div>
    `;
}

function renderReport(data) {
    const reportContainer = document.getElementById('reportContainer');
    let xaiImageHTML = '';
    if (data.xai_image_url) {
        xaiImageHTML = `
            <div class="report-section">
                <h4>Model Attention (XAI)</h4>
                <p>The highlighted areas are what the AI focused on to make its diagnosis.</p>
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

function attachNavListeners() {
    document.querySelectorAll('nav a, nav button').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = e.currentTarget.dataset.view;
            renderView(viewId);
        });
    });
}

function attachDiagnosisListeners() {
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const reportContainer = document.getElementById('reportContainer');

    imageUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.hidden = false;
                getGPSAndDiagnose(file);
            };
            reader.readAsDataURL(file);
        }
    });

    function getGPSAndDiagnose(file) {
        loadingIndicator.classList.remove('hidden');
        reportContainer.innerHTML = '';

        const accessToken = localStorage.getItem('accessToken');
        if (!accessToken) {
            alert("Your session has expired. Please log in again.");
            logout();
            return;
        }

        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            loadingIndicator.classList.add('hidden');
            return;
        }

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
                    const response = await fetch(DIAGNOSE_API_URL, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${accessToken}`
                        },
                        body: formData
                    });
                    const data = await response.json();
                    if (!response.ok) throw new Error(data.detail || 'Diagnosis failed');
                    renderReport(data);
                } catch (error) {
                    reportContainer.innerHTML = `<p class="error-message">${error.message}</p>`;
                } finally {
                    loadingIndicator.classList.add('hidden');
                }
            },
            () => {
                alert("Unable to retrieve your location. Please enable location services.");
                loadingIndicator.classList.add('hidden');
            }
        );
    }
}

function logout() {
    localStorage.removeItem('accessToken');
    window.location.href = 'login.html';
}