// ====================================================================
//  frontend/dashboard.js (Final Two-Page Version)
// ====================================================================

// --- 1. CONFIGURATION & GLOBAL STATE ---
const API_BASE_URL = 'https://juliette-unattempted-tammara.ngrok-free.dev';
const USERS_ME_API_URL = `${API_BASE_URL}/users/me`;
const USERS_API_URL = `${API_BASE_URL}/users/`;
const DIAGNOSE_API_URL = `${API_BASE_URL}/diagnose`;
const DIAGNOSES_HISTORY_API_URL = `${API_BASE_URL}/diagnoses/me`;
const POSTS_API_URL = `${API_BASE_URL}/posts/`;
const PRODUCTS_API_URL = `${API_BASE_URL}/products/`;
const ORDERS_API_URL = `${API_BASE_URL}/orders/`;
const SUBSCRIPTION_API_URL = `${API_BASE_URL}/users/me/subscription`;
const CHAT_API_URL = `${API_BASE_URL}/chat`;

let currentUser = null;
let websocket = null;

// --- 2. INITIALIZATION ON PAGE LOAD (with Auth Guard) ---

document.addEventListener('DOMContentLoaded', async () => {
    const appContainer = document.getElementById('app-container');
    appContainer.innerHTML = `<div style="display: flex; justify-content: center; align-items: center; height: 100vh;"><div class="spinner"></div></div>`;

    let accessToken = localStorage.getItem('accessToken');
    const urlParams = new URLSearchParams(window.location.search);
    const justLoggedIn = urlParams.get('loggedin') === 'true';

    // 【【【 核心修复 2: 新的守卫逻辑 】】】
    if (!accessToken && !justLoggedIn) {
        window.location.href = './index.html';
        return;
    }

    if (justLoggedIn && !accessToken) {
        await new Promise(resolve => setTimeout(resolve, 150));
        accessToken = localStorage.getItem('accessToken');
    }

    if (!accessToken) {
        alert('Login failed. Please try again.');
        window.location.href = './index.html';
        return;
    }

    try {
        currentUser = await apiFetch(accessToken, USERS_ME_API_URL);
        renderDashboard(currentUser);
    } catch (e) {
        console.error("Session is invalid or expired:", e);
        // apiFetch in dashboard.js handles logout on 401
    }
});


// --- 3. CORE HELPERS ---

async function apiFetch(token, url, options = {}) {
    // 【【【 在这里添加修复代码 】】】
    const defaultHeaders = { 
        'Authorization': `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true' // <-- 添加这一行
    };
    // 【【【 修复结束 】】】

    if (!(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }
    const config = { ...options, headers: { ...defaultHeaders, ...options.headers }, cache: 'no-cache' };

    try {
        const response = await fetch(url, config);

        const contentLength = response.headers.get('content-length');
        if (response.status === 204 || contentLength === '0') {
            return null;
        }

        if (!response.ok) {
            if (response.status === 401) {
                console.error("API returned 401 Unauthorized. Logging out.");
                logout();
                throw new Error("Session expired. Please log in again.");
            }
            const errorData = await response.json().catch(() => ({ 
                detail: `The server responded with status: ${response.status}` 
            }));
            throw new Error(errorData.detail);
        }
        
        return await response.json();

    } catch (networkError) {
        console.error("API Fetch Error:", networkError);
        throw networkError;
    }
}

function logout() {
    if (websocket) websocket.close();
    localStorage.removeItem('accessToken');
    window.location.href = './index.html';
}


// --- 4. UI RENDERING FUNCTIONS ---

function renderDashboard(user) {
    const appContainer = document.getElementById('app-container');
    appContainer.innerHTML = '';
    const dashboardContainer = document.createElement('div');
    dashboardContainer.className = 'dashboard-container';
    
    const header = document.createElement('header');
    const { permissions, user_type, email } = user;
    
    let navLinks = `
        <a href="#" class="nav-link" data-view="profile">Profile</a>
        <a href="#" class="nav-link active-link" data-view="ai-diagnosis">AI Diagnosis</a>
        <a href="#" class="nav-link" data-view="diagnosis-history">History</a>
        <a href="#" class="nav-link ${!permissions.can_like_share ? 'disabled-link' : ''}" data-view="posts">Posts</a>
        <a href="#" class="nav-link ${!permissions.can_shop ? 'disabled-link' : ''}" data-view="shopping">Shopping</a>
        <a href="#" class="nav-link ${!permissions.can_chat ? 'disabled-link' : ''}" data-view="chat">Chat</a>
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
    renderView(urlParams.get('view') || 'ai-diagnosis', urlParams.get('userId'));
}

async function renderView(viewId, param) {
    const mainContent = document.getElementById('mainContent');
    const token = localStorage.getItem('accessToken');
    if (!mainContent || !token) return;

    mainContent.innerHTML = `<div class="card full-width" style="text-align: center;"><div class="spinner"></div></div>`;

    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active-link');
        if (link.dataset.view === viewId) {
            link.classList.add('active-link');
        }
    });

    if (websocket && viewId !== 'chat') {
        websocket.close();
        websocket = null;
    }

    try {
        if (viewId === 'chat') await renderChatView(param);
        else if (viewId === 'ai-diagnosis') { mainContent.innerHTML = getAIDiagnosisHTML(); attachDiagnosisListeners(); }
        else if (viewId === 'diagnosis-history') { const history = await apiFetch(token, DIAGNOSES_HISTORY_API_URL); mainContent.innerHTML = getDiagnosisHistoryHTML(history); }
        else if (viewId === 'posts') { const posts = await apiFetch(token, POSTS_API_URL); mainContent.innerHTML = getPostsHTML(posts); attachPostListeners(); }
        else if (viewId === 'shopping') { const products = await apiFetch(token, PRODUCTS_API_URL); mainContent.innerHTML = getShoppingHTML(products); attachShoppingListeners(); }
        else if (viewId === 'business-profile' && currentUser.user_type === 'business') { const myProducts = await apiFetch(token, `${API_BASE_URL}/products/me`); mainContent.innerHTML = getBusinessProfileHTML(myProducts); attachAddProductListeners(); }
        else if (viewId === 'profile') { currentUser = await apiFetch(token, USERS_ME_API_URL); mainContent.innerHTML = getProfileHTML(currentUser); attachPlanButtonListeners(); }
        else mainContent.innerHTML = `<div class="card full-width"><p>Content for this view is coming soon.</p></div>`;
    } catch (error) {
        mainContent.innerHTML = `<div class="card full-width error-message"><p>Failed to load view: ${error.message}</p></div>`;
    }
}

async function renderUserProfileView(userId) {
    const mainContent = document.getElementById('mainContent');
    const token = localStorage.getItem('accessToken');
    mainContent.innerHTML = `<div class="card full-width" style="text-align: center;"><div class="spinner"></div></div>`;
    try {
        const userProfile = await apiFetch(token, `${USERS_API_URL}${userId}/profile`);
        const avatarUrl = userProfile.avatar_url ? `${API_BASE_URL}${userProfile.avatar_url}` : `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.name)}&background=random&color=fff&size=128`;
        mainContent.innerHTML = `
            <div class="card full-width" style="max-width: 600px; margin: auto; text-align: center;">
                <img src="${avatarUrl}" class="avatar" style="width: 100px; height: 100px; margin-bottom: 20px;">
                <h3>${userProfile.name}</h3>
                <p><strong>User Type:</strong> ${userProfile.user_type}</p>
                <button class="glow-button" id="startChatBtn" data-user-id="${userProfile.id}">Start Chat</button>
            </div>
        `;
        document.getElementById('startChatBtn').addEventListener('click', (e) => {
            renderView('chat', e.currentTarget.dataset.userId);
        });
    } catch (error) {
        mainContent.innerHTML = `<div class="card full-width error-message"><p>Failed to load user profile: ${error.message}</p></div>`;
    }
}

// --- 5. HTML TEMPLATE GENERATORS (All functions are complete) ---
function getAIDiagnosisHTML() {
    return `<div class="card full-width"><h3>AI Diagnosis</h3><div class="input-group" style="margin-bottom: 20px; max-width: 300px;"><label for="languageSelect" style="display: block; margin-bottom: 5px; color: var(--text-secondary);">Report Language:</label><select id="languageSelect"><option value="en">English</option><option value="ms">Bahasa Malaysia</option><option value="zh">Chinese (简体中文)</option></select></div><label for="imageUpload" class="diagnosis-uploader"><p>Click here to upload a leaf photo for analysis</p><img id="imagePreview" src="" alt="Image preview" hidden></label><input type="file" id="imageUpload" accept="image/*"><div id="loadingIndicator" class="hidden"><div class="spinner"></div><p>Analyzing... This may take a moment.</p></div><div id="reportContainer"></div></div>`;
}

function getDiagnosisHistoryHTML(history) {
    if (!history || history.length === 0) return `<div class="card full-width"><h3>Diagnosis History</h3><p>No diagnosis history found.</p></div>`;
    return `<div class="view-content">${history.map(item => `<div class="card"><img src="${API_BASE_URL}${item.image_url}" style="width:100%; border-radius:8px; margin-bottom: 15px;"><h4>${item.report_title}</h4><p><strong>Result:</strong> ${item.disease_name} (${(item.confidence * 100).toFixed(2)}%)</p><p style="font-size: 0.9em; color: var(--text-secondary);"><strong>Date:</strong> ${new Date(item.timestamp).toLocaleString()}</p></div>`).join('')}</div>`;
}

function getPostsHTML(posts) {
    let html = `<h3>Community Posts</h3>`;
    if (currentUser.permissions.can_post) {
        html += `<div class="card create-post-card"><form id="createPostForm"><textarea name="content" placeholder="Share your thoughts, ${currentUser.email}..." required></textarea><div class="post-form-actions"><label for="postImageUpload" class="action-btn">📷 Add Photo</label><input type="file" name="image" id="postImageUpload" class="hidden" accept="image/*"><button type="button" id="addLocationBtn" class="action-btn">📍 Add Location</button><input type="text" name="location" id="postLocation" placeholder="e.g., Sibu, Sarawak" class="hidden"><button type="submit" class="glow-button">Post</button></div><p class="error-message" id="post-error"></p></form></div>`;
    }
    if (!posts || posts.length === 0) {
        html += `<div class="card"><p>No posts yet. Be the first to share!</p></div>`;
    } else {
        html += posts.map(post => {
            const isLiked = post.likes.some(like => like.user_id === currentUser.id);
            const ownerName = post.owner.profile ? post.owner.profile.name : post.owner.email;
            const avatarUrl = post.owner.profile && post.owner.profile.avatar_url ? `${API_BASE_URL}${post.owner.profile.avatar_url}` : `https://ui-avatars.com/api/?name=${encodeURIComponent(ownerName)}&background=random&color=fff`;
            return `<div class="card post-card" data-post-id="${post.id}"><div class="post-header"><a href="#" class="user-profile-link" data-user-id="${post.owner.id}"><img src="${avatarUrl}" class="avatar"></a><div><a href="#" class="user-profile-link post-owner-name" data-user-id="${post.owner.id}"><strong>${ownerName}</strong></a>${post.location ? `<span class="post-location"> - at ${post.location}</span>` : ''}<div class="post-timestamp">${new Date(post.created_at).toLocaleString()}</div></div></div><p class="post-content">${post.content}</p>${post.image_url ? `<img src="${API_BASE_URL}${post.image_url}" class="post-image">` : ''}<div class="post-actions">${currentUser.permissions.can_like_share ? `<button class="action-btn like-btn ${isLiked ? 'liked' : ''}">👍 Like (${post.likes.length})</button><button class="action-btn share-btn">🔗 Share</button>` : ''}</div><div class="comments-section">${post.comments.map(c => `<div class="comment"><p><small><strong>${c.owner.profile ? c.owner.profile.name : c.owner.email}:</strong> ${c.content}</small></p></div>`).join('')}${currentUser.permissions.can_comment ? `<form class="comment-form"><input type="text" name="content" placeholder="Write a comment..."><button type="submit" class="send-btn">Send</button></form>` : ''}</div></div>`;
        }).join('');
    }
    return html;
}

function getShoppingHTML(products) {
    let html = `<h3>Marketplace</h3>`;
    if (!products || products.length === 0) {
        html += `<p>No products available right now.</p>`;
    } else {
        const productCards = products.map(p => `<div class="card product-card"><img src="${API_BASE_URL}${p.image_url}" style="width:100%; height: 200px; object-fit: cover; border-radius:8px;"><h4>${p.name}</h4><p style="color: var(--text-secondary);">${p.description || ''}</p><p><strong>RM ${p.price.toFixed(2)}</strong></p><button class="glow-button buy-btn" data-product-id="${p.id}" data-product-name="${p.name}" data-price="${p.price.toFixed(2)}">Buy Now</button></div>`).join('');
        html = `<div class="view-content">${productCards}</div>`;
    }
    return `<div class="card full-width">${html}</div>`;
}

function getBusinessProfileHTML(myProducts) {
    let myProductsHTML = `<h4>My Products</h4>`;
    if (!myProducts || myProducts.length === 0) {
        myProductsHTML += `<p>You haven't added any products yet.</p>`;
    } else {
        myProductsHTML += myProducts.map(p => `<div class="product-list-item" style="display: flex; gap: 15px; align-items: center; margin-bottom: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px;"><img src="${API_BASE_URL}${p.image_url}" style="width: 50px; height: 50px; border-radius: 4px; object-fit: cover;"><span>${p.name} - RM ${p.price.toFixed(2)}</span></div>`).join('');
    }
    return `<div class="view-content"><div class="card"><h3>Income</h3><p>Coming Soon.</p></div><div class="card"><h3>Product Sell Quantity</h3><p>Coming Soon.</p></div><div class="card"><h3>Add Product to Sell</h3><form id="addProductForm"><input type="text" name="name" placeholder="Product Name" required><textarea name="description" placeholder="Description" style="min-height: 80px; resize: vertical;"></textarea><input type="text" name="location" placeholder="Location"><input type="number" name="price" placeholder="Price (RM)" step="0.01" required><label class="file-input-label">Product Picture <input type="file" name="image" class="file-input" required></label><button type="submit" class="glow-button">Add Product</button><p id="product-error" class="error-message"></p></form></div><div class="card full-width">${myProductsHTML}</div></div>`;
}

function getProfileHTML(user) {
    const tier = user.subscription_tier || 'free';
    let planName = 'Free Tier';
    if (tier === 'tier_10') planName = 'Pro (RM10)';
    else if (tier === 'tier_15') planName = 'Pro Plus (RM15)';
    else if (tier === 'tier_20') planName = 'Business Pro (RM20)';
    let planButtonsHTML = '';
    if (user.user_type === 'public') {
        if (tier !== 'tier_10') planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_10">Subscribe to RM10 Plan</button>`;
        if (tier !== 'tier_15') planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_15">${tier === 'tier_10' ? 'Upgrade to RM15 Plan' : 'Subscribe to RM15 Plan'}</button>`;
    }
    if (user.user_type === 'business' && tier !== 'tier_20') {
        planButtonsHTML += `<button class="glow-button plan-btn" data-plan="tier_20">Subscribe to RM20 Business Plan</button>`;
    }
    if (tier !== 'free') {
        planButtonsHTML += `<button class="plan-btn-secondary plan-btn" data-plan="free">Downgrade to Free Tier</button>`;
    }
    return `<div class="card full-width"><h3>My Profile</h3><p><strong>Email:</strong> ${user.email}</p><p><strong>User Type:</strong> ${user.user_type}</p><p><strong>Current Plan:</strong> ${planName}</p><h4 style="margin-top: 30px;">Change Plan</h4><div class="plans" style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">${planButtonsHTML}</div><p id="payment-error" class="error-message"></p></div>`;
}

function renderReport(data) {
    let xaiImageHTML = '';
    if (data.xai_image_url) {
        xaiImageHTML = `<div class="report-section"><h4>Model Attention (XAI)</h4><p>The highlighted areas are what the AI focused on.</p><img id="xaiImage" src="${API_BASE_URL}${data.xai_image_url}" alt="XAI Heatmap"></div>`;
    }
    document.getElementById('reportContainer').innerHTML = `<div class="report-section"><h3>${data.title}</h3></div><div class="report-section"><h4>Diagnosis Summary</h4><p>${data.diagnosis_summary}</p></div><div class="report-section"><h4>Environmental Context</h4><p>${data.environmental_context}</p></div>${xaiImageHTML}<div class="report-section"><h4>Management Suggestions</h4><div id="reportSuggestion">${data.management_suggestion.replace(/\n/g, '<br>')}</div></div>`;
}

function getChatHTML() {
    return `<div class="chat-container"><div id="chat-sidebar" class="card"><h3>Conversations</h3><div id="user-list"><div class="spinner"></div></div></div><div id="chat-window" class="card"><div id="chat-header">Select a conversation</div><div id="messages"><p class="chat-placeholder">Select a conversation to start chatting.</p></div><form id="chat-form" class="hidden"><input type="text" id="message-input" placeholder="Type a message..." autocomplete="off" required><button type="submit" class="send-btn glow-button">Send</button></form></div></div>`;
}

async function renderChatView(targetUserId = null) {
    document.getElementById('mainContent').innerHTML = getChatHTML();
    const token = localStorage.getItem('accessToken');
    connectWebSocket(token);
    const userListDiv = document.getElementById('user-list');
    try {
        const users = await apiFetch(token, USERS_API_URL);
        userListDiv.innerHTML = users.map(user => `<div class="user-list-item" data-user-id="${user.id}" data-user-name="${user.profile.name}"><img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.profile.name)}&background=random&color=fff" class="avatar"><span>${user.profile.name}</span></div>`).join('');
        document.querySelectorAll('.user-list-item').forEach(item => {
            item.addEventListener('click', () => {
                item.classList.remove('new-message');
                openChat(item.dataset.userId, item.dataset.userName);
            });
        });
        if (targetUserId) {
            const targetUserItem = document.querySelector(`.user-list-item[data-user-id='${targetUserId}']`);
            if (targetUserItem) {
                targetUserItem.classList.remove('new-message');
                openChat(targetUserId, targetUserItem.dataset.userName);
            }
        }
    } catch (error) {
        userListDiv.innerHTML = `<p class="error-message">Could not load users.</p>`;
    }
}

async function openChat(userId, userName) {
    document.getElementById('chat-header').textContent = `Chat with ${userName}`;
    const messagesDiv = document.getElementById('messages');
    const token = localStorage.getItem('accessToken');
    messagesDiv.innerHTML = '<div class="spinner"></div>';
    const chatForm = document.getElementById('chat-form');
    chatForm.classList.remove('hidden');
    chatForm.dataset.recipientId = userId;
    document.querySelectorAll('.user-list-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`.user-list-item[data-user-id='${userId}']`).classList.add('active');
    try {
        const history = await apiFetch(token, `${CHAT_API_URL}/history/${userId}`);
        messagesDiv.innerHTML = '';
        if (history.length === 0) {
            messagesDiv.innerHTML = '<p class="chat-placeholder">This is the beginning of your conversation.</p>';
        } else {
            history.forEach(msg => appendMessage(msg.content, msg.sender_id === currentUser.id ? 'sent' : 'received'));
        }
    } catch (error) {
        messagesDiv.innerHTML = `<p class="error-message">Could not load chat history.</p>`;
    }
    const newChatForm = chatForm.cloneNode(true);
    chatForm.parentNode.replaceChild(newChatForm, chatForm);
    newChatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        if (message && websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ recipient_id: parseInt(userId), content: message }));
            appendMessage(message, 'sent');
            input.value = '';
        }
    });
}

function appendMessage(content, type) {
    const messagesDiv = document.getElementById('messages');
    const placeholder = messagesDiv.querySelector('.chat-placeholder');
    if (placeholder) placeholder.remove();
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', type);
    messageElement.textContent = content;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function connectWebSocket(token) {
    if (websocket && websocket.readyState === WebSocket.OPEN) return;

    // 【【【 核心修复：智能判断使用 ws:// 还是 wss:// 】】】
    
    // 1. 获取后端服务器的主机名 (例如: juliette-unattempted-tammara.ngrok-free.dev)
    const backendHost = API_BASE_URL.replace('https://', '').replace('http://', '');

    // 2. 判断当前页面是否是 HTTPS
    const isSecure = window.location.protocol === 'https:';

    // 3. 根据页面安全协议，选择对应的 WebSocket 协议
    const wsProtocol = isSecure ? 'wss' : 'ws';

    // 4. 构建最终的、正确的 WebSocket URL
    const wsUrl = `${wsProtocol}://${backendHost}/chat/ws?token=${token}`;
    
    // 【【【 修复结束 】】】

    console.log(`Attempting to connect to WebSocket at: ${wsUrl}`); // 添加日志方便调试

    websocket = new WebSocket(wsUrl);
    websocket.onopen = () => console.log("WebSocket connected!");
    websocket.onmessage = (event) => {
        const messageData = JSON.parse(event.data);
        const chatForm = document.getElementById('chat-form');
        const currentRecipientId = chatForm ? chatForm.dataset.recipientId : null;
        if (String(messageData.sender_id) === currentRecipientId) {
            appendMessage(messageData.content, 'received');
        } else {
            const senderItem = document.querySelector(`.user-list-item[data-user-id='${messageData.sender_id}']`);
            if (senderItem) senderItem.classList.add('new-message');
        }
    };
    websocket.onclose = () => console.log("WebSocket disconnected.");
    websocket.onerror = (error) => console.error("WebSocket error:", error);
}

function showOrderModal(product) {
    const oldModal = document.getElementById('orderModal');
    if (oldModal) oldModal.remove();
    const modal = document.createElement('div');
    modal.id = 'orderModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `<div class="modal-content card"><button class="close-modal">&times;</button><h3>Checkout: ${product.name}</h3><p>Price: RM <span id="modalPrice">${product.price}</span></p><form id="orderForm"><h4>1. Shipping Information</h4><input type="text" name="recipient_name" placeholder="Full Name" required><input type="tel" name="recipient_phone" placeholder="Phone Number" required><textarea name="shipping_address" placeholder="Shipping Address" required></textarea><div class="input-group"><label for="quantity">Quantity:</label><input type="number" id="quantity" name="quantity" value="1" min="1" required></div><h3 style="margin-top: 20px;">Total: RM <span id="totalPrice">${product.price}</span></h3><h4>2. Payment Method</h4><select id="paymentMethodSelect" name="payment_method" required><option value="spay">SPay Global</option><option value="tng">Touch 'n Go eWallet</option><option value="bank">Online Banking</option></select><div id="paymentDetails"><div id="spay-details" class="payment-option"><p>Please scan the QR code below to pay:</p><img src="/assets/Spay.jpg" alt="SPay QR Code" class="qr-code"></div><div id="tng-details" class="payment-option hidden"><p>Please scan with your TnG eWallet to pay:</p><img src="/assets/TnG.jpg" alt="TnG QR Code" class="qr-code"></div><div id="bank-details" class="payment-option hidden"><div class="bank-choice"><button type="button" class="bank-option-btn active" data-method="qr">Scan QR Code</button><button type="button" class="bank-option-btn" data-method="manual">Bank Account Number</button></div><div id="bank-qr" class="bank-method"><p>Please scan the DuitNow QR code to pay:</p><img src="/assets/DuitNow.jpg" alt="Maybank DuitNow QR" class="qr-code"></div><div id="bank-manual" class="bank-method hidden"><select name="bank_type"><option>Maybank</option><option>Public Bank</option><option>Hong Leong Bank</option><option>Bank Islam</option></select><input type="text" name="account_number" placeholder="Enter 16-digit Account Number" pattern="[0-9]{16}" title="Please enter exactly 16 digits"></div></div></div><button type="submit" class="glow-button">I Have Paid, Confirm Purchase</button><p id="order-error" class="error-message"></p></form></div>`;
    document.body.appendChild(modal);
    const closeModal = () => modal.remove();
    modal.querySelector('.close-modal').onclick = closeModal;
    modal.onclick = (e) => { if (e.target === modal) closeModal(); };
    const quantityInput = modal.querySelector('#quantity');
    const totalPriceSpan = modal.querySelector('#totalPrice');
    quantityInput.addEventListener('input', () => {
        totalPriceSpan.textContent = ((parseInt(quantityInput.value) || 0) * parseFloat(product.price)).toFixed(2);
    });
    const paymentSelect = modal.querySelector('#paymentMethodSelect');
    paymentSelect.addEventListener('change', () => {
        const selectedMethod = paymentSelect.value;
        modal.querySelectorAll('.payment-option').forEach(opt => opt.classList.add('hidden'));
        document.getElementById(`${selectedMethod}-details`).classList.remove('hidden');
    });
    modal.querySelectorAll('.bank-option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            modal.querySelectorAll('.bank-option-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const method = btn.dataset.method;
            modal.querySelectorAll('.bank-method').forEach(m => m.classList.add('hidden'));
            document.getElementById(`bank-${method}`).classList.remove('hidden');
        });
    });
    modal.querySelector('#orderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorP = document.getElementById('order-error');
        errorP.textContent = 'Processing...';
        const formData = new FormData(e.target);
        const token = localStorage.getItem('accessToken');
        if (formData.get('payment_method') === 'bank' && document.querySelector('.bank-option-btn[data-method="manual"]').classList.contains('active')) {
            if (!/^\d{16}$/.test(formData.get('account_number'))) {
                errorP.textContent = 'Invalid account number. Must be 16 digits.';
                return;
            }
        }
        const orderData = { recipient_name: formData.get('recipient_name'), recipient_phone: formData.get('recipient_phone'), shipping_address: formData.get('shipping_address'), items: [{ product_id: parseInt(product.id), quantity: parseInt(formData.get('quantity')) }] };
        try {
            const result = await apiFetch(token, ORDERS_API_URL, { method: 'POST', body: JSON.stringify(orderData) });
            alert(`Purchase successful! Your order ID is #${result.id}.`);
            closeModal();
        } catch (error) {
            errorP.textContent = `Purchase failed: ${error.message}`;
        }
    });
}

// --- 6. EVENT LISTENERS & INTERACTION LOGIC ---

function attachNavListeners() {
    document.querySelectorAll('nav a, nav button').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.currentTarget.classList.contains('disabled-link')) {
                alert('This feature is not available for your current subscription plan.');
                return;
            }
            renderView(e.currentTarget.dataset.view);
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
    const token = localStorage.getItem('accessToken');
    loadingIndicator.classList.remove('hidden');
    reportContainer.innerHTML = '';
    navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            const formData = new FormData();
            formData.append("image", file);
            formData.append("latitude", latitude);
            formData.append("longitude", longitude);
            formData.append("language", document.getElementById('languageSelect').value);
            try {
                const data = await apiFetch(token, DIAGNOSE_API_URL, { method: 'POST', body: formData });
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
    const token = localStorage.getItem('accessToken');
    document.querySelectorAll('.plan-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            if (e.target.disabled) return;
            const plan = e.target.dataset.plan;
            const errorP = document.getElementById('payment-error');
            errorP.textContent = '';
            const planDisplayName = plan === 'free' ? 'Free Tier' : plan.replace('tier_', 'RM ');
            if (!confirm(`Are you sure you want to switch to the ${planDisplayName} plan?`)) return;
            try {
                // 1. 发送请求并获取最新的用户信息
                currentUser = await apiFetch(token, SUBSCRIPTION_API_URL, { method: 'PUT', body: JSON.stringify({ plan: plan }) });
                
                // 2. 弹出成功提示
                alert('Plan updated successfully!');
    
                // 3. 【【【 核心修复 】】】
                //    使用最新的 currentUser 数据，重新渲染整个仪表盘界面
                renderDashboard(currentUser); 
            
            } catch (error) {
                errorP.textContent = `Failed to update plan: ${error.message}`;
            }
        });
    });
}

function attachPostListeners() {
    const postForm = document.getElementById('createPostForm');
    const token = localStorage.getItem('accessToken');
    if (postForm) {
        const addLocationBtn = document.getElementById('addLocationBtn');
        const postLocationInput = document.getElementById('postLocation');
        addLocationBtn.addEventListener('click', () => {
            if (!postLocationInput.classList.contains('hidden')) {
                postLocationInput.classList.add('hidden');
                postLocationInput.value = '';
                addLocationBtn.textContent = '📍 Add Location';
                return;
            }
            if (confirm("Use current GPS location? Press 'Cancel' to enter manually.")) {
                if (!navigator.geolocation) { alert("Geolocation is not supported."); return; }
                addLocationBtn.textContent = 'Fetching...';
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        postLocationInput.value = `Lat: ${position.coords.latitude.toFixed(4)}, Lon: ${position.coords.longitude.toFixed(4)}`;
                        postLocationInput.classList.remove('hidden');
                        addLocationBtn.textContent = '📍 Location Added';
                    },
                    () => {
                        alert("Unable to retrieve location. Please enter manually.");
                        postLocationInput.classList.remove('hidden');
                        postLocationInput.focus();
                        addLocationBtn.textContent = '📍 Add Location';
                    }
                );
            } else {
                postLocationInput.classList.remove('hidden');
                postLocationInput.focus();
            }
        });
        postForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await apiFetch(token, POSTS_API_URL, { method: 'POST', body: new FormData(postForm) });
                renderView('posts');
            } catch (error) {
                document.getElementById('post-error').textContent = `Failed to post: ${error.message}`;
            }
        });
    }
    document.querySelectorAll('.post-card').forEach(card => {
        const postId = card.dataset.postId;
        const commentForm = card.querySelector('.comment-form');
        if (commentForm) {
            commentForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const content = commentForm.querySelector('input[name="content"]').value;
                if (!content.trim()) return;
                try {
                    await apiFetch(token, `${POSTS_API_URL}${postId}/comments/`, { method: 'POST', body: JSON.stringify({ content: content }) });
                    renderView('posts');
                } catch (error) {
                    alert(`Failed to comment: ${error.message}`);
                }
            });
        }
        const likeBtn = card.querySelector('.like-btn');
        if (likeBtn) {
            likeBtn.addEventListener('click', async () => {
                try {
                    await apiFetch(token, `${POSTS_API_URL}${postId}/like`, { method: 'POST' });
                    renderView('posts');
                } catch (error) {
                    alert(`Failed to like post: ${error.message}`);
                }
            });
        }
        const shareBtn = card.querySelector('.share-btn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(`${window.location.origin}${window.location.pathname}?view=post&id=${postId}`)
                    .then(() => alert('Post link copied!'))
                    .catch(() => alert('Failed to copy.'));
            });
        }
        card.querySelectorAll('.user-profile-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                renderUserProfileView(e.currentTarget.dataset.userId);
            });
        });
    });
}

function attachShoppingListeners() {
    document.querySelectorAll('.buy-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const product = {
                id: e.target.dataset.productId,
                name: e.target.dataset.productName,
                price: e.target.dataset.price
            };
            showOrderModal(product);
        });
    });
}

function attachAddProductListeners() {
    const productForm = document.getElementById('addProductForm');
    const token = localStorage.getItem('accessToken');
    if (productForm) {
        productForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const errorP = document.getElementById('product-error');
            errorP.textContent = '';
            try {
                await apiFetch(token, PRODUCTS_API_URL, { method: 'POST', body: new FormData(productForm) });
                alert('Product added successfully!');
                renderView('business-profile');
            } catch (error) {
                errorP.textContent = `Failed to add product: ${error.message}`;
            }
        });
    }
}