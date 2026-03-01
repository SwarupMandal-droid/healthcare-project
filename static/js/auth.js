let currentRole = null;

// ---- Role Selection ----
function selectRole(role) {
    currentRole = role;

    // Highlight selected card
    document.querySelectorAll('.role-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.role === role);
    });

    // Short delay for visual feedback, then transition
    setTimeout(() => goToStep('stepForm'), 350);

    // Update left panel
    updateLeftPanel(role);

    // Update role badge on form
    const badge = document.getElementById('selectedRoleBadge');
    const labels = { patient: '👤 Patient', doctor: '🩺 Doctor', admin: '🛡️ Admin' };
    badge.textContent = labels[role];
    badge.className = `selected-role-badge ${role}`;

    // Set hidden role inputs
    document.getElementById('loginRole').value = role;
    document.getElementById('signupRole').value = role;

    // Show/hide role-specific fields
    document.getElementById('doctorFields').style.display = role === 'doctor' ? 'block' : 'none';
    document.getElementById('patientFields').style.display = role === 'patient' ? 'block' : 'none';
}

// ---- Step Navigation ----
function goToStep(stepId) {
    document.querySelectorAll('.auth-step').forEach(s => s.classList.remove('active'));
    document.getElementById(stepId).classList.add('active');

    const backBtn = document.getElementById('backBtn');
    backBtn.classList.toggle('visible', stepId !== 'stepRole');
}

function goBack() {
    goToStep('stepRole');
    updateLeftPanel('role');
    currentRole = null;
}

// ---- Update Left Panel ----
function updateLeftPanel(step) {
    document.querySelectorAll('.left-step').forEach(s => s.classList.remove('active'));
    const target = document.querySelector(`.left-step[data-step="${step}"]`);
    if (target) target.classList.add('active');
}

// ---- Tab Switching ----
function switchTab(tab) {
    const loginForm  = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const tabLogin   = document.getElementById('tabLogin');
    const tabSignup  = document.getElementById('tabSignup');
    const slider     = document.getElementById('tabSlider');

    if (tab === 'login') {
        loginForm.classList.add('active');
        signupForm.classList.remove('active');
        tabLogin.classList.add('active');
        tabSignup.classList.remove('active');
        slider.classList.remove('right');
    } else {
        signupForm.classList.add('active');
        loginForm.classList.remove('active');
        tabSignup.classList.add('active');
        tabLogin.classList.remove('active');
        slider.classList.add('right');
    }
}

// ---- Toggle Password Visibility ----
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon  = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// ---- Password Strength ----
document.addEventListener('DOMContentLoaded', function () {

    const pwInput = document.getElementById('signupPassword');
    const pwFill  = document.getElementById('pwFill');
    const pwLabel = document.getElementById('pwLabel');

    if (pwInput) {
        pwInput.addEventListener('input', function () {
            const val = this.value;
            let strength = 0;

            if (val.length >= 8)                       strength++;
            if (/[A-Z]/.test(val))                     strength++;
            if (/[0-9]/.test(val))                     strength++;
            if (/[^A-Za-z0-9]/.test(val))             strength++;

            const levels = [
                { width: '0%',   color: '',              label: 'Enter password' },
                { width: '25%',  color: '#EF4444',       label: 'Weak' },
                { width: '50%',  color: '#F59E0B',       label: 'Fair' },
                { width: '75%',  color: '#3B82F6',       label: 'Good' },
                { width: '100%', color: '#10B981',       label: 'Strong 💪' },
            ];

            const level = levels[strength];
            pwFill.style.width      = level.width;
            pwFill.style.background = level.color;
            pwLabel.textContent     = level.label;
            pwLabel.style.color     = level.color || 'var(--gray-500)';
        });
    }

    // ---- Form Validation & Submit ----

    // LOGIN
    const loginFormEl = document.getElementById('loginFormEl');
    if (loginFormEl) {
        loginFormEl.addEventListener('submit', function (e) {
            e.preventDefault();
            let valid = true;

            const email = this.email.value.trim();
            const pw    = this.password.value;

            clearErrors('login');

            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                showError('loginEmailError', 'Please enter a valid email address');
                valid = false;
            }
            if (!pw || pw.length < 6) {
                showError('loginPwError', 'Password must be at least 6 characters');
                valid = false;
            }

            if (valid) submitForm('login', this);
        });
    }

    // SIGNUP
    const signupFormEl = document.getElementById('signupFormEl');
    if (signupFormEl) {
        signupFormEl.addEventListener('submit', function (e) {
            e.preventDefault();
            let valid = true;

            const name    = this.name.value.trim();
            const email   = this.email.value.trim();
            const pw      = this.password.value;
            const confirm = document.getElementById('confirmPassword').value;
            const terms   = this.terms.checked;

            clearErrors('signup');

            if (!name || name.length < 2) {
                showError('signupNameError', 'Please enter your full name');
                valid = false;
            }
            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                showError('signupEmailError', 'Please enter a valid email address');
                valid = false;
            }
            if (!pw || pw.length < 8) {
                showError('signupPwError', 'Password must be at least 8 characters');
                valid = false;
            }
            if (pw !== confirm) {
                showError('confirmPwError', 'Passwords do not match');
                valid = false;
            }
            if (!terms) {
                alert('Please accept the Terms of Service to continue.');
                valid = false;
            }

            if (valid) submitForm('signup', this);
        });
    }

});

// ---- Helper: Show error ----
function showError(id, msg) {
    const el = document.getElementById(id);
    if (el) {
        el.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${msg}`;
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.gap = '4px';
        el.style.marginTop = '6px';
    }
}

// ---- Helper: Clear errors ----
function clearErrors(prefix) {
    const ids = prefix === 'login'
        ? ['loginEmailError', 'loginPwError']
        : ['signupNameError', 'signupEmailError', 'signupPwError', 'confirmPwError'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '';
    });
}

// ---- Real form submission ----
function submitForm(type, form) {
    const btn     = document.getElementById(type === 'login' ? 'loginBtn' : 'signupBtn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.btn-spinner');

    // Show loading state
    btnText.style.display = 'none';
    spinner.style.display = 'inline';
    btn.disabled = true;

    // Submit the real form
    form.submit();
}
