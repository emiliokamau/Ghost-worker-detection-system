/**
 * BioGuard Frontend Logic
 * Handles navigation, API interactions, and UI updates
 */

// API Base URL
const API_URL = 'http://localhost:5000/api';

// State
let currentState = {
    currentTab: 'dashboard',
    cameraActive: false,
    capturedImage: null,
    employees: [],
    stats: {},
    alerts: []
};

// DOM Elements
const elements = {
    navItems: document.querySelectorAll('.nav-item'),
    views: document.querySelectorAll('.view'),
    pageTitle: document.getElementById('current-page-title'),
    currentDate: document.getElementById('current-date'),

    // Dashboard
    statEmployees: document.getElementById('stat-employees'),
    statAttendance: document.getElementById('stat-attendance'),
    statDuplicates: document.getElementById('stat-duplicates'),
    statGhosts: document.getElementById('stat-ghosts'),
    recentActivityTable: document.getElementById('recent-activity-table'),
    generateDataBtn: document.getElementById('generate-data-btn'),

    // Registration
    regForm: document.getElementById('registration-form'),
    photoCaptureCard: document.getElementById('photo-capture-card'),
    photoUpload: document.getElementById('photo-upload'),
    photoPreview: document.getElementById('photo-preview'),
    capturePreview: document.getElementById('capture-preview'),

    // Verification
    startCameraBtn: document.getElementById('start-camera'),
    captureBtn: document.getElementById('capture-btn'),
    cameraFeed: document.getElementById('camera-feed'),
    verificationPreview: document.getElementById('verification-preview'),
    verificationResult: document.getElementById('verification-result'),

    // Employees
    employeesTableBody: document.getElementById('employees-table-body'),

    // Fraud
    fraudAlertsList: document.getElementById('fraud-alerts-list'),
    ghostWorkersTable: document.getElementById('ghost-workers-table')
};

// Authentication
// const auth = {
//     user: null,
//
//     async check() {
//         try {
//             const response = await fetch(`${API_URL}/check-auth`);
//             if (response.ok) {
//                 const data = await response.json();
//                 this.user = data.user;
//                 this.updateUI(true);
//             } else {
//                 this.updateUI(false);
//             }
//         } catch (error) {
//             console.error('Auth check failed:', error);
//             this.updateUI(false);
//         }
//     },
//
//     async login(email, password) {
//         try {
//             const response = await fetch(`${API_URL}/login`, {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ email, password })
//             });
//
//             const data = await response.json();
//
//             if (response.ok) {
//                 this.user = data.user;
//                 this.updateUI(true);
//                 return { success: true };
//             } else {
//                 return { success: false, error: data.error };
//             }
//         } catch (error) {
//         },
//
//     async logout() {
//             try {
//                 await fetch(`${API_URL}/logout`, { method: 'POST' });
//                 this.user = null;
//                 this.updateUI(false);
//             } catch (error) {
//                 console.error('Logout failed:', error);
//             }
//         },
//
//         updateUI(isLoggedIn) {
//             const modal = document.getElementById('login-modal');
//             const profileName = document.querySelector('.user-info h4');
//             const profileRole = document.querySelector('.user-info span');
//             const profileImg = document.querySelector('.user-profile img');
//
//             if (isLoggedIn) {
//                 modal.classList.add('hidden');
//                 if (this.user) {
//                     profileName.textContent = this.user.username;
//                     profileRole.textContent = this.user.role === 'admin' ? 'System Administrator' : 'User';
//                     profileImg.src = `https://ui-avatars.com/api/?name=${this.user.username}&background=0D8ABC&color=fff`;
//                 }
//                 // Load initial data
//                 loadDashboardData();
//             } else {
//                 modal.classList.remove('hidden');
//                 // Clear sensitive data
//                 elements.recentActivityTable.innerHTML = '';
// document.getElementById('login-form').addEventListener('submit', async (e) => {
//     e.preventDefault();
//     const email = document.getElementById('login-email').value;
//     const password = document.getElementById('login-password').value;
//     const errorMsg = document.getElementById('login-error');
//     const btn = e.target.querySelector('button');
//
//     btn.disabled = true;
//     btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...';
//
//     const result = await auth.login(email, password);
//
//     if (!result.success) {
//         errorMsg.textContent = result.error;
//         errorMsg.classList.remove('hidden');
//         btn.disabled = false;
//         btn.textContent = 'Login';
//     } else {
//         errorMsg.classList.add('hidden');
//         // Reset button state handled by UI update
//         btn.disabled = false;
//         btn.textContent = 'Login';
//     }
// });

// Signup Form
// document.getElementById('signup-form').addEventListener('submit', async (e) => {
//     e.preventDefault();
//     const username = document.getElementById('signup-username').value;
//     const email = document.getElementById('signup-email').value;
//     const phone = document.getElementById('signup-phone').value;
//     const password = document.getElementById('signup-password').value;
//     const confirm = document.getElementById('signup-confirm').value;
//     const errorMsg = document.getElementById('signup-error');
//     const btn = e.target.querySelector('button');
//
//     if (password !== confirm) {
//         errorMsg.textContent = "Passwords do not match";
//         errorMsg.classList.remove('hidden');
//         return;
//     }
//
//     btn.disabled = true;
//     btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';
//
//     const result = await auth.signup(username, password, email, phone);
//
//     if (!result.success) {
//         errorMsg.textContent = result.error;
//         errorMsg.classList.remove('hidden');
//         btn.disabled = false;
//         btn.textContent = 'Register Admin';
//     } else {
//         errorMsg.classList.add('hidden');
//         btn.disabled = false;
//         btn.textContent = 'Register Admin';
//
//         // Redirect to login
//         alert('Registration successful! Please login with your email and password.');
//         document.getElementById('signup-form').reset();
//         document.getElementById('show-login').click(); // Switch to login view
//     }
// });

// Toggle Login/Signup
document.getElementById('show-signup').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('signup-form').style.display = 'block';
    document.querySelector('.brand-header h2').innerHTML = '<i class="fa-solid fa-user-plus"></i> Admin Register';
    document.querySelector('.brand-header p').textContent = 'Create New Admin Account';
});

document.getElementById('show-login').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('signup-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
    document.querySelector('.brand-header h2').innerHTML = 'BioGuard';
    document.querySelector('.brand-header p').textContent = 'Admin Access Required';
});

// Generate Data
elements.generateDataBtn.addEventListener('click', async () => {
    // if (!auth.user) return; // Guard disabled

    const btn = elements.generateDataBtn;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;

    try {
        await fetch(`${API_URL}/generate-sample-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_employees: 5 })
        });

        // Refresh dashboard
        await loadDashboardData();
        alert('Sample data generated successfully!');
    } catch (error) {
        console.error('Error generating data:', error);
        alert('Failed to generate data');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
});

// ... (Rest of event listeners)

// Registration Photo Upload
elements.photoCaptureCard.addEventListener('click', () => {
    elements.photoUpload.click();
});

elements.photoUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.photoPreview.src = e.target.result;
            elements.capturePreview.classList.remove('hidden');
            elements.photoCaptureCard.querySelector('.status-badge').textContent = 'Captured';
            elements.photoCaptureCard.querySelector('.status-badge').classList.add('success');
            elements.photoCaptureCard.querySelector('.status-badge').classList.remove('pending');
        };
        reader.readAsDataURL(file);
    }
});

// Registration Form Submit
elements.regForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(elements.regForm);
    const data = Object.fromEntries(formData.entries());

    // Add photo data if exists
    if (elements.photoPreview.src) {
        data.photo_data = elements.photoPreview.src;
    }

    // Simulate fingerprint
    data.fingerprint_data = 'simulated_fingerprint_' + Date.now();

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Employee registered successfully!');
            elements.regForm.reset();
            elements.capturePreview.classList.add('hidden');
            if (result.duplicates_found > 0) {
                alert(`Warning: ${result.duplicates_found} potential duplicates detected!`);
            }
        } else {
            alert('Registration failed: ' + result.error);
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration');
    }
});

// Verification Camera
elements.startCameraBtn.addEventListener('click', startCamera);
elements.captureBtn.addEventListener('click', captureAndVerify);
}

// ... (Rest of functions)

window.resolveAlert = async function (alertId) {
    if (confirm('Mark this alert as resolved?')) {
        try {
            await fetch(`${API_URL}/duplicates/${alertId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'resolved', notes: 'Resolved by admin' })
            });
            loadFraudData();
            loadDashboardData();
        } catch (error) {
            console.error('Error resolving alert:', error);
        }
    }
};
