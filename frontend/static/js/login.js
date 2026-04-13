// 登录页面 JavaScript

const API_BASE = '';

// Tab 切换
document.addEventListener('DOMContentLoaded', () => {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;

            // 更新 tab 状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 显示对应表单
            if (tab === 'login') {
                loginForm.style.display = 'flex';
                registerForm.style.display = 'none';
            } else {
                loginForm.style.display = 'none';
                registerForm.style.display = 'flex';
            }
        });
    });

    // 登录表单提交
    loginForm.addEventListener('submit', handleLogin);

    // 注册表单提交
    registerForm.addEventListener('submit', handleRegister);

    // 检查是否已登录
    checkAuth();
});

function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
        const response = await fetch('/api/auth/me', {
            headers: getAuthHeader()
        });
        if (response.ok) {
            window.location.href = '/index';
        } else {
            localStorage.removeItem('access_token');
        }
    } catch (e) {
        localStorage.removeItem('access_token');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('login-error');
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    console.log('尝试登录:', username);
    errorDiv.textContent = '';

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        console.log('登录响应状态:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('登录成功，Token:', data.access_token ? '已获取' : '未获取');
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/index';
        } else {
            const data = await response.json();
            console.log('登录失败:', data.detail);
            errorDiv.textContent = data.detail || '登录失败';
        }
    } catch (e) {
        console.error('登录错误:', e);
        errorDiv.textContent = '网络错误，请重试';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const errorDiv = document.getElementById('register-error');
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;

    errorDiv.textContent = '';

    // 验证
    if (password !== confirmPassword) {
        errorDiv.textContent = '两次输入的密码不一致';
        return;
    }

    if (password.length < 6) {
        errorDiv.textContent = '密码长度至少6个字符';
        return;
    }

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            alert('注册成功，请登录');
            // 切换到登录 tab
            document.querySelector('[data-tab="login"]').click();
            document.getElementById('login-username').value = username;
        } else {
            const data = await response.json();
            errorDiv.textContent = data.detail || '注册失败';
        }
    } catch (e) {
        errorDiv.textContent = '网络错误，请重试';
    }
}
