// FloatChat ARGO Ocean Data System
class FloatChatApp {
    constructor() {
        this.currentUser = null;
        this.currentPage = 'home';
        this.chatHistory = [];
        this.argoFloats = [
            {id: '2901623', lat: -10.5, lng: 67.8, status: 'active', temp: 28.5, salinity: 35.1},
            {id: '2901624', lat: -15.2, lng: 72.1, status: 'active', temp: 27.8, salinity: 35.3},
            {id: '2901625', lat: -8.7, lng: 65.3, status: 'active', temp: 29.1, salinity: 34.9},
            {id: '2901626', lat: -12.8, lng: 70.5, status: 'maintenance', temp: 25.2, salinity: 35.0},
            {id: '2901627', lat: -6.2, lng: 68.9, status: 'active', temp: 28.8, salinity: 35.2}
        ];
        this.init();
    }

    init() {
        this.showPage('home');
        this.checkAuthStatus();
    }

    checkAuthStatus() {
        const token = localStorage.getItem('authToken');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                if (payload.exp > Date.now() / 1000) {
                    this.currentUser = payload;
                    this.updateNavigation();
                }
            } catch (e) {
                localStorage.removeItem('authToken');
            }
        }
    }

    updateNavigation() {
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');

        if (this.currentUser) {
            loginBtn.classList.add('hidden');
            logoutBtn.classList.remove('hidden');
        } else {
            loginBtn.classList.remove('hidden');
            logoutBtn.classList.add('hidden');
        }
    }

    showPage(page) {
        this.currentPage = page;
        const content = document.getElementById('main-content');

        switch (page) {
            case 'home':
                content.innerHTML = this.renderHomePage();
                break;
            case 'about':
                content.innerHTML = this.renderAboutPage();
                break;
            case 'contact':
                content.innerHTML = this.renderContactPage();
                break;
            case 'login':
                this.showAuthModal();
                break;
            case 'user':
                content.innerHTML = this.renderUserDashboard();
                this.showUserContent('chat');
                break;
            case 'admin':
                content.innerHTML = this.renderAdminDashboard();
                this.showAdminContent('chatbot-db');
                break;
        }
    }

    renderHomePage() {
        return `
            <div class="hero">
                <div class="container">
                    <h1>FloatChat ARGO Ocean Intelligence</h1>
                    <p>AI-powered conversational interface for exploring global ocean data from ARGO floats</p>
                    <div class="hero-actions">
                        <button class="btn btn--primary btn--lg" onclick="app.showPage('login')">Get Started</button>
                        <button class="btn btn--outline btn--lg" onclick="app.showPage('about')">Learn More</button>
                    </div>
                </div>
            </div>

            <div class="container">
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">🤖</div>
                        <h3>AI Chatbot</h3>
                        <p>Ask questions about ocean data using natural language and get intelligent responses</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🌊</div>
                        <h3>ARGO Float Tracking</h3>
                        <p>Monitor and visualize thousands of autonomous ocean profiling floats worldwide</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">📊</div>
                        <h3>Data Visualization</h3>
                        <p>Interactive maps and charts for temperature, salinity, and ocean profile analysis</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderAboutPage() {
        return `
            <div class="container">
                <div class="card">
                    <h2>About FloatChat ARGO</h2>
                    <p>FloatChat is an AI-powered platform that democratizes access to ARGO ocean data through conversational interfaces and interactive visualizations.</p>

                    <h3>What are ARGO Floats?</h3>
                    <p>ARGO floats are autonomous instruments that drift with ocean currents, diving to depths of 2000m to collect temperature, salinity, and other oceanographic data. They surface every 10 days to transmit data via satellite.</p>

                    <h3>Features</h3>
                    <ul>
                        <li>Natural language queries about ocean data</li>
                        <li>Interactive mapping of float locations</li>
                        <li>Profile visualization and comparison</li>
                        <li>Data export capabilities</li>
                        <li>Real-time data updates</li>
                    </ul>
                </div>
            </div>
        `;
    }

    renderContactPage() {
        return `
            <div class="container">
                <div class="card">
                    <h2>Contact Us</h2>
                    <div class="form-group">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control" placeholder="Your name">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" placeholder="your@email.com">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Message</label>
                        <textarea class="form-control" rows="4" placeholder="Your message"></textarea>
                    </div>
                    <button class="btn btn--primary">Send Message</button>
                </div>
            </div>
        `;
    }

    showAuthModal() {
        const modal = document.getElementById('authModal');
        const modalBody = document.getElementById('modalBody');

        modalBody.innerHTML = `
            <h2>Login to FloatChat</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label class="form-label">Username</label>
                    <input type="text" id="username" class="form-control" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn--primary">Login</button>
            </form>

            <div class="mt-2">
                <p>Demo Credentials:</p>
                <p><strong>User:</strong> user / user123</p>
                <p><strong>Admin:</strong> admin / admin123</p>
            </div>
        `;

        modal.classList.remove('hidden');

        document.getElementById('loginForm').onsubmit = (e) => {
            e.preventDefault();
            this.handleLogin();
        };
    }

    hideModal() {
        document.getElementById('authModal').classList.add('hidden');
    }

    handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Demo authentication
        const demoUsers = {
            'user': { password: 'user123', role: 'user', name: 'Marine Researcher' },
            'admin': { password: 'admin123', role: 'admin', name: 'System Administrator' }
        };

        if (demoUsers[username] && demoUsers[username].password === password) {
            this.currentUser = {
                username,
                role: demoUsers[username].role,
                name: demoUsers[username].name
            };

            // Store auth token
            const token = btoa(JSON.stringify({
                ...this.currentUser,
                exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour
            }));
            localStorage.setItem('authToken', token);

            this.hideModal();
            this.updateNavigation();
            this.showPage(this.currentUser.role);
        } else {
            alert('Invalid credentials');
        }
    }

    logout() {
        this.currentUser = null;
        localStorage.removeItem('authToken');
        this.updateNavigation();
        this.showPage('home');
    }

    renderUserDashboard() {
        return `
            <div class="sidebar">
                <h3>User Dashboard</h3>
                <ul class="sidebar-menu">
                    <li><button onclick="app.showUserContent('chat')">🤖 Chatbot</button></li>
                    <li><button onclick="app.showUserContent('argo-map')">📍 ARGO Locations</button></li>
                    <li><button onclick="app.showUserContent('ocean-map')">🌊 Ocean Map</button></li>
                    <li><button onclick="app.showUserContent('profile')">👤 Profile</button></li>
                </ul>
            </div>
            <div class="main-content">
                <div id="user-content"></div>
            </div>
        `;
    }

    renderAdminDashboard() {
        return `
            <div class="sidebar">
                <h3>Admin Dashboard</h3>
                <ul class="sidebar-menu">
                    <li><button onclick="app.showAdminContent('chatbot-db')">🤖 Update Chatbot DB</button></li>
                    <li><button onclick="app.showAdminContent('nc-converter')">📁 NC to CSV Converter</button></li>
                    <li><button onclick="app.showAdminContent('system')">⚙️ System Status</button></li>
                    <li><button onclick="app.showAdminContent('users')">👥 User Management</button></li>
                </ul>
            </div>
            <div class="main-content">
                <div id="admin-content"></div>
            </div>
        `;
    }

    showUserContent(type) {
        const content = document.getElementById('user-content');

        switch (type) {
            case 'chat':
                content.innerHTML = this.renderChatInterface();
                break;
            case 'argo-map':
                content.innerHTML = this.renderArgoMap();
                setTimeout(() => this.initializeMap(), 100);
                break;
            case 'ocean-map':
                content.innerHTML = this.renderOceanMap();
                break;
            case 'profile':
                content.innerHTML = this.renderUserProfile();
                break;
        }
    }

    showAdminContent(type) {
        const content = document.getElementById('admin-content');

        switch (type) {
            case 'chatbot-db':
                content.innerHTML = this.renderChatbotDB();
                break;
            case 'nc-converter':
                content.innerHTML = this.renderNCConverter();
                break;
            case 'system':
                content.innerHTML = this.renderSystemStatus();
                break;
            case 'users':
                content.innerHTML = this.renderUserManagement();
                break;
        }
    }

    renderChatInterface() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ARGO Data Chatbot</h3>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages">
                        <div class="message bot">
                            <p>Hello! I'm your ARGO data assistant. Ask me about ocean temperature, salinity, float locations, or any oceanographic data questions.</p>
                        </div>
                    </div>
                    <div class="chat-input-container">
                        <input type="text" class="form-control chat-input" id="chatInput" placeholder="Ask about ARGO data...">
                        <button class="btn btn--primary" onclick="app.sendChatMessage()">Send</button>
                    </div>
                </div>
            </div>
        `;
    }

    renderArgoMap() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">ARGO Float Locations</h3>
                    <span>${this.argoFloats.length} Active Floats</span>
                </div>
                <div id="argoMap" class="map-container"></div>
                <div class="mt-2">
                    <h4>Float Status</h4>
                    <div id="floatList"></div>
                </div>
            </div>
        `;
    }

    renderOceanMap() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Ocean Data Visualization</h3>
                </div>
                <p>Interactive ocean data visualization coming soon...</p>
                <div id="oceanChart" style="height: 300px; background: #f0f8ff; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                    <p>Temperature & Salinity Charts</p>
                </div>
            </div>
        `;
    }

    renderUserProfile() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">User Profile</h3>
                </div>
                <p><strong>Name:</strong> ${this.currentUser.name}</p>
                <p><strong>Username:</strong> ${this.currentUser.username}</p>
                <p><strong>Role:</strong> ${this.currentUser.role}</p>
                <p><strong>Chat Sessions:</strong> ${this.chatHistory.length}</p>
            </div>
        `;
    }

    renderChatbotDB() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Update Chatbot Database</h3>
                </div>
                <div class="form-group">
                    <label class="form-label">Training Data (JSON)</label>
                    <textarea class="form-control" rows="10" id="trainingData" placeholder='[{"question": "What is temperature?", "answer": "Temperature is..."}]'></textarea>
                </div>
                <button class="btn btn--primary" onclick="app.updateChatbotDB()">Update Database</button>
                <div id="updateStatus" class="mt-2"></div>
            </div>
        `;
    }

    renderNCConverter() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">NetCDF to CSV Converter</h3>
                </div>
                <div class="form-group">
                    <label class="form-label">Select NetCDF Files</label>
                    <input type="file" class="form-control" id="ncFiles" multiple accept=".nc">
                </div>
                <button class="btn btn--primary" onclick="app.convertNCFiles()">Convert to CSV</button>
                <div id="conversionStatus" class="mt-2"></div>
                <div id="conversionResults" class="mt-2"></div>
            </div>
        `;
    }

    renderSystemStatus() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">System Status</h3>
                </div>
                <div class="features-grid">
                    <div class="card">
                        <h4>Database</h4>
                        <p>MySQL: Connected</p>
                        <p>MongoDB: Connected</p>
                        <p>Vector DB: Active</p>
                    </div>
                    <div class="card">
                        <h4>Statistics</h4>
                        <p>Total Floats: ${this.argoFloats.length}</p>
                        <p>Active Users: 2</p>
                        <p>Chat Sessions: ${this.chatHistory.length}</p>
                    </div>
                </div>
            </div>
        `;
    }

    renderUserManagement() {
        return `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">User Management</h3>
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <th style="text-align: left; padding: 0.5rem;">Username</th>
                            <th style="text-align: left; padding: 0.5rem;">Role</th>
                            <th style="text-align: left; padding: 0.5rem;">Status</th>
                            <th style="text-align: left; padding: 0.5rem;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 0.5rem;">user</td>
                            <td style="padding: 0.5rem;">User</td>
                            <td style="padding: 0.5rem;">Active</td>
                            <td style="padding: 0.5rem;"><button class="btn btn--outline">Edit</button></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 0.5rem;">admin</td>
                            <td style="padding: 0.5rem;">Admin</td>
                            <td style="padding: 0.5rem;">Active</td>
                            <td style="padding: 0.5rem;"><button class="btn btn--outline">Edit</button></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message) return;

        const messagesContainer = document.getElementById('chatMessages');

        // Add user message
        messagesContainer.innerHTML += `
            <div class="message user">
                <p>${message}</p>
            </div>
        `;

        // Generate bot response
        const response = this.generateChatResponse(message);

        setTimeout(() => {
            messagesContainer.innerHTML += `
                <div class="message bot">
                    <p>${response}</p>
                </div>
            `;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 1000);

        this.chatHistory.push({ user: message, bot: response, timestamp: new Date() });
        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    generateChatResponse(query) {
        const responses = {
            'temperature': `I found temperature data from ${this.argoFloats.length} active floats. Average surface temperature is 28.1°C with variations from 25°C to 29°C. The thermocline typically occurs around 80-120m depth.`,
            'salinity': `Salinity measurements show typical values of 34.9-35.3 PSU across the monitored region. Higher salinity is observed in the Arabian Sea due to evaporation effects.`,
            'location': `Currently tracking ${this.argoFloats.length} ARGO floats across the Indian Ocean. Most recent data shows floats distributed between 6°S-16°S latitude and 65°E-73°E longitude.`,
            'float': `ARGO float network includes ${this.argoFloats.filter(f => f.status === 'active').length} active floats. Each float profiles to 2000m depth every 10 days, collecting T/S data.`,
            'profile': `Ocean profiles show typical tropical stratification with warm surface waters (28-29°C), sharp thermocline (100-200m), and cooler deep waters (2-4°C at 2000m).`
        };

        const queryLower = query.toLowerCase();
        for (const [key, response] of Object.entries(responses)) {
            if (queryLower.includes(key)) {
                return response;
            }
        }

        return `I can help you explore ARGO float data including temperature, salinity, and location information. Try asking about specific parameters like "show temperature profiles" or "where are the nearest floats".`;
    }

    initializeMap() {
        const map = L.map('argoMap').setView([-10, 68], 6);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        this.argoFloats.forEach(float => {
            const color = float.status === 'active' ? 'green' : 'orange';
            const marker = L.circleMarker([float.lat, float.lng], {
                color: color,
                fillColor: color,
                fillOpacity: 0.7,
                radius: 8
            }).addTo(map);

            marker.bindPopup(`
                <b>Float ${float.id}</b><br>
                Status: ${float.status}<br>
                Temperature: ${float.temp}°C<br>
                Salinity: ${float.salinity} PSU
            `);
        });

        // Update float list
        const floatList = document.getElementById('floatList');
        floatList.innerHTML = this.argoFloats.map(float => `
            <div style="padding: 0.5rem; border: 1px solid #ddd; margin: 0.25rem; border-radius: 4px;">
                <strong>${float.id}</strong> - ${float.status} - ${float.temp}°C, ${float.salinity} PSU
            </div>
        `).join('');
    }

    updateChatbotDB() {
        const trainingData = document.getElementById('trainingData').value;
        const statusDiv = document.getElementById('updateStatus');

        try {
            JSON.parse(trainingData);
            statusDiv.innerHTML = '<div style="color: green;">✓ Chatbot database updated successfully!</div>';
        } catch (e) {
            statusDiv.innerHTML = '<div style="color: red;">✗ Invalid JSON format</div>';
        }
    }

    convertNCFiles() {
        const files = document.getElementById('ncFiles').files;
        const statusDiv = document.getElementById('conversionStatus');
        const resultsDiv = document.getElementById('conversionResults');

        if (files.length === 0) {
            statusDiv.innerHTML = '<div style="color: red;">Please select NetCDF files</div>';
            return;
        }

        statusDiv.innerHTML = '<div style="color: blue;">Converting files...</div>';

        setTimeout(() => {
            statusDiv.innerHTML = '<div style="color: green;">✓ Conversion completed!</div>';
            resultsDiv.innerHTML = `
                <h4>Conversion Results</h4>
                ${Array.from(files).map(file => `
                    <div style="padding: 0.5rem; border: 1px solid #ddd; margin: 0.25rem; border-radius: 4px;">
                        ${file.name} → ${file.name.replace('.nc', '.csv')} ✓
                    </div>
                `).join('')}
            `;
        }, 2000);
    }
}

// Global functions
function showPage(page) {
    app.showPage(page);
}

function hideModal() {
    app.hideModal();
}

function logout() {
    app.logout();
}

// Initialize app
const app = new FloatChatApp();

// Handle chat input on Enter key
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.target.id === 'chatInput') {
            app.sendChatMessage();
        }
    });
});