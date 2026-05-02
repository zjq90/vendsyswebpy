// API基础地址
const API_BASE = window.location.origin;

// 存储token的key
const TOKEN_KEY = 'vending_token';
const USER_INFO_KEY = 'vending_user_info';
const USER_MENUS_KEY = 'vending_user_menus';

// ==================== HTTP请求工具 ====================

/**
 * 通用HTTP请求
 */
async function httpRequest(url, options = {}) {
    const token = getToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        method: options.method || 'GET',
        headers: {
            ...defaultHeaders,
            ...options.headers
        },
        ...options
    };
    
    if (options.data) {
        config.body = JSON.stringify(options.data);
    }
    
    try {
        const response = await fetch(url, config);
        
        // 处理401未授权
        if (response.status === 401) {
            clearStorage();
            if (!window.location.pathname.includes('login.html')) {
                alert('登录已过期，请重新登录');
                window.location.href = '/static/login.html';
            }
            return null;
        }
        
        // 处理403无权限
        if (response.status === 403) {
            const result = await response.json();
            showToast(result.message || '无权限访问', 'error');
            return null;
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('HTTP请求错误:', error);
        showToast('网络请求失败，请检查网络连接', 'error');
        return null;
    }
}

/**
 * GET请求
 */
async function httpGet(url, params = {}) {
    // 构建查询字符串
    const queryString = Object.keys(params)
        .filter(key => params[key] !== undefined && params[key] !== null && params[key] !== '')
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
        .join('&');
    
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    
    return httpRequest(fullUrl, {
        method: 'GET'
    });
}

/**
 * POST请求
 */
async function httpPost(url, data = {}) {
    return httpRequest(url, {
        method: 'POST',
        data: data
    });
}

/**
 * PUT请求
 */
async function httpPut(url, data = {}) {
    return httpRequest(url, {
        method: 'PUT',
        data: data
    });
}

/**
 * DELETE请求
 */
async function httpDelete(url) {
    return httpRequest(url, {
        method: 'DELETE'
    });
}

// ==================== Token和用户信息管理 ====================

/**
 * 获取token
 */
function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * 保存token
 */
function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

/**
 * 保存用户信息
 */
function setUserInfo(userInfo) {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
}

/**
 * 获取用户信息
 */
function getUserInfo() {
    const info = localStorage.getItem(USER_INFO_KEY);
    return info ? JSON.parse(info) : null;
}

/**
 * 保存菜单
 */
function setMenus(menus) {
    localStorage.setItem(USER_MENUS_KEY, JSON.stringify(menus));
}

/**
 * 获取菜单
 */
function getMenus() {
    const menus = localStorage.getItem(USER_MENUS_KEY);
    return menus ? JSON.parse(menus) : [];
}

/**
 * 清除存储
 */
function clearStorage() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
    localStorage.removeItem(USER_MENUS_KEY);
}

/**
 * 检查登录状态
 */
function checkLogin() {
    const token = getToken();
    if (!token) {
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = '/static/login.html';
        }
        return false;
    }
    return true;
}

// ==================== 提示消息 ====================

/**
 * 显示Toast提示
 */
function showToast(message, type = 'info') {
    // 创建toast容器
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(container);
    }
    
    // 创建toast元素
    const toast = document.createElement('div');
    
    // 设置颜色
    let bgColor, borderColor;
    switch (type) {
        case 'success':
            bgColor = '#d4edda';
            borderColor = '#28a745';
            break;
        case 'error':
            bgColor = '#f8d7da';
            borderColor = '#dc3545';
            break;
        case 'warning':
            bgColor = '#fff3cd';
            borderColor = '#ffc107';
            break;
        default:
            bgColor = '#d1ecf1';
            borderColor = '#17a2b8';
    }
    
    toast.style.cssText = `
        padding: 12px 20px;
        margin-bottom: 10px;
        border-radius: 4px;
        background-color: ${bgColor};
        border-left: 4px solid ${borderColor};
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // 3秒后移除
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

/**
 * 显示确认对话框
 */
function showConfirm(message, title = '确认') {
    return new Promise((resolve) => {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // 创建对话框
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 20px;
            min-width: 300px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        `;
        
        dialog.innerHTML = `
            <h5 style="margin: 0 0 15px 0; font-weight: bold;">${title}</h5>
            <p style="margin: 0 0 20px 0; color: #666;">${message}</p>
            <div style="text-align: right;">
                <button class="btn btn-secondary" style="margin-right: 10px;" id="confirm-cancel">取消</button>
                <button class="btn btn-danger" id="confirm-ok">确认</button>
            </div>
        `;
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        // 绑定事件
        document.getElementById('confirm-cancel').onclick = () => {
            overlay.remove();
            resolve(false);
        };
        
        document.getElementById('confirm-ok').onclick = () => {
            overlay.remove();
            resolve(true);
        };
    });
}

// ==================== 表格分页 ====================

/**
 * 渲染分页
 */
function renderPagination(containerId, currentPage, totalPages, total, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = `
        <span style="color: #666; margin-right: 15px;">共 ${total} 条记录</span>
        <ul class="pagination pagination-sm" style="margin: 0;">
    `;
    
    // 上一页
    if (currentPage > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage - 1}">上一页</a></li>`;
    } else {
        html += `<li class="page-item disabled"><span class="page-link">上一页</span></li>`;
    }
    
    // 页码
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
    }
    
    // 下一页
    if (currentPage < totalPages) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${currentPage + 1}">下一页</a></li>`;
    } else {
        html += `<li class="page-item disabled"><span class="page-link">下一页</span></li>`;
    }
    
    html += `</ul>`;
    container.innerHTML = html;
    
    // 绑定点击事件
    container.querySelectorAll('a.page-link').forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            const page = parseInt(link.dataset.page);
            if (onPageChange) {
                onPageChange(page);
            }
        };
    });
}

// ==================== 表单工具 ====================

/**
 * 从表单获取数据
 */
function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const data = {};
    const elements = form.querySelectorAll('input, select, textarea');
    
    elements.forEach(el => {
        if (el.name && el.name !== '') {
            if (el.type === 'checkbox') {
                data[el.name] = el.checked;
            } else if (el.type === 'number') {
                data[el.name] = el.value === '' ? null : Number(el.value);
            } else {
                data[el.name] = el.value;
            }
        }
    });
    
    return data;
}

/**
 * 设置表单数据
 */
function setFormData(formId, data) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    Object.keys(data).forEach(key => {
        const el = form.querySelector(`[name="${key}"]`);
        if (el) {
            if (el.type === 'checkbox') {
                el.checked = !!data[key];
            } else if (el.type === 'select-multiple') {
                // 多选框
                Array.from(el.options).forEach(opt => {
                    opt.selected = data[key] && data[key].includes(opt.value);
                });
            } else {
                el.value = data[key] || '';
            }
        }
    });
}

/**
 * 清空表单
 */
function clearForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.reset();
}

// ==================== 日期工具 ====================

/**
 * 格式化日期
 */
function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '';
    
    const d = new Date(date);
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const minute = String(d.getMinutes()).padStart(2, '0');
    const second = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hour)
        .replace('mm', minute)
        .replace('ss', second);
}

/**
 * 获取今天日期字符串
 */
function getTodayDate() {
    return formatDate(new Date(), 'YYYY-MM-DD');
}

/**
 * 获取N天前的日期
 */
function getDaysAgoDate(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return formatDate(d, 'YYYY-MM-DD');
}

// ==================== 加载状态 ====================

/**
 * 显示加载状态
 */
function showLoading(containerId) {
    const container = containerId ? document.getElementById(containerId) : document.body;
    if (!container) return;
    
    const loading = document.createElement('div');
    loading.id = 'global-loading';
    loading.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Loading...</span>
            </div>
            <p style="margin-top: 10px; color: #666;">加载中...</p>
        </div>
    `;
    
    container.innerHTML = '';
    container.appendChild(loading);
}

/**
 * 隐藏加载状态
 */
function hideLoading(containerId) {
    const loading = document.getElementById('global-loading');
    if (loading) {
        loading.remove();
    }
}

// ==================== 侧边栏菜单 ====================

/**
 * 渲染侧边栏菜单
 */
function renderSidebarMenu() {
    const menus = getMenus();
    const userInfo = getUserInfo();
    
    const sidebarMenu = document.getElementById('sidebar-menu');
    if (!sidebarMenu) return;
    
    // 构建菜单HTML
    let html = '';
    
    // 仪表盘/首页
    html += `
        <li class="nav-item">
            <a href="index.html" class="nav-link ${window.location.pathname.includes('index.html') ? 'active' : ''}">
                <i class="nav-icon fas fa-tachometer-alt"></i>
                <p>仪表盘</p>
            </a>
        </li>
    `;
    
    // 系统管理菜单项
    html += `<li class="nav-header">系统管理</li>`;
    
    // 渲染用户菜单
    menus.forEach(menu => {
        const hasChildren = menu.children && menu.children.length > 0;
        const isActive = isMenuActive(menu);
        
        if (hasChildren) {
            // 有子菜单
            html += `
                <li class="nav-item ${isActive ? 'menu-open' : ''}">
                    <a href="#" class="nav-link ${isActive ? 'active' : ''}" onclick="toggleSubmenu(this, event)">
                        <i class="nav-icon ${menu.icon || 'fas fa-circle'}"></i>
                        <p>
                            ${menu.name}
                            <i class="right fas fa-angle-left"></i>
                        </p>
                    </a>
                    <ul class="nav nav-treeview" style="${isActive ? 'display: block;' : 'display: none;'}">
            `;
            
            menu.children.forEach(child => {
                const childActive = window.location.pathname.includes(child.path || '');
                html += `
                    <li class="nav-item">
                        <a href="${child.path || '#'}" class="nav-link ${childActive ? 'active' : ''}">
                            <i class="far fa-circle nav-icon"></i>
                            <p>${child.name}</p>
                        </a>
                    </li>
                `;
            });
            
            html += `</ul></li>`;
        } else {
            // 没有子菜单
            html += `
                <li class="nav-item">
                    <a href="${menu.path || '#'}" class="nav-link ${isActive ? 'active' : ''}">
                        <i class="nav-icon ${menu.icon || 'fas fa-circle'}"></i>
                        <p>${menu.name}</p>
                    </a>
                </li>
            `;
        }
    });
    
    // 可视化大屏（单独添加，不在权限菜单中）
    html += `
        <li class="nav-item">
            <a href="dashboard-screen.html" class="nav-link ${window.location.pathname.includes('dashboard-screen.html') ? 'active' : ''}">
                <i class="nav-icon fas fa-desktop"></i>
                <p>可视化大屏</p>
            </a>
        </li>
    `;
    
    sidebarMenu.innerHTML = html;
}

/**
 * 检查菜单是否激活
 */
function isMenuActive(menu) {
    if (window.location.pathname.includes(menu.path || '')) {
        return true;
    }
    if (menu.children) {
        return menu.children.some(child => 
            window.location.pathname.includes(child.path || '')
        );
    }
    return false;
}

/**
 * 切换子菜单
 */
function toggleSubmenu(element, event) {
    event.preventDefault();
    
    const parent = element.closest('.nav-item');
    const submenu = parent.querySelector('.nav-treeview');
    const icon = element.querySelector('.right');
    
    if (submenu.style.display === 'none') {
        submenu.style.display = 'block';
        parent.classList.add('menu-open');
        icon.classList.remove('fa-angle-left');
        icon.classList.add('fa-angle-down');
    } else {
        submenu.style.display = 'none';
        parent.classList.remove('menu-open');
        icon.classList.remove('fa-angle-down');
        icon.classList.add('fa-angle-left');
    }
}

/**
 * 初始化头部用户信息
 */
function initHeaderUserInfo() {
    const userInfo = getUserInfo();
    if (!userInfo) return;
    
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) {
        userDropdown.innerHTML = `
            <img src="https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=user%20avatar%20icon%20simple&image_size=square" 
                 class="img-circle elevation-2" alt="User Image" 
                 style="width: 25px; height: 25px; object-fit: cover;">
            <span class="d-none d-md-inline" style="margin-left: 5px;">${userInfo.real_name || userInfo.username}</span>
        `;
    }
    
    // 初始化退出登录按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.onclick = async () => {
            const confirmed = await showConfirm('确定要退出登录吗？', '退出确认');
            if (confirmed) {
                const result = await httpPost(`${API_BASE}/api/auth/logout`);
                clearStorage();
                showToast('已退出登录', 'success');
                setTimeout(() => {
                    window.location.href = '/static/login.html';
                }, 500);
            }
        };
    }
}

/**
 * 初始化页面（非登录页）
 */
function initPage() {
    // 检查登录
    if (!checkLogin()) return;
    
    // 渲染菜单
    renderSidebarMenu();
    
    // 初始化头部
    initHeaderUserInfo();
}

// ==================== 表单验证工具 ====================

/**
 * 表单验证器对象
 */
const Validator = {
    // 验证规则
    rules: {
        required: (value) => {
            return value !== null && value !== undefined && value !== '';
        },
        minLength: (value, min) => {
            return value && value.length >= min;
        },
        maxLength: (value, max) => {
            return value && value.length <= max;
        },
        phone: (value) => {
            const phoneRegex = /^1[3-9]\d{9}$/;
            return !value || phoneRegex.test(value);
        },
        email: (value) => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return !value || emailRegex.test(value);
        },
        password: (value) => {
            if (!value) return false;
            if (value.length < 6) return false;
            if (value.length > 32) return false;
            return true;
        },
        strongPassword: (value) => {
            if (!Validator.rules.password(value)) return false;
            const hasUpperCase = /[A-Z]/.test(value);
            const hasLowerCase = /[a-z]/.test(value);
            const hasNumber = /\d/.test(value);
            const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
            return hasUpperCase && hasLowerCase && hasNumber && (hasSpecialChar || value.length >= 12);
        },
        username: (value) => {
            if (!value) return false;
            const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
            return usernameRegex.test(value);
        },
        match: (value, compareValue) => {
            return value === compareValue;
        },
        number: (value, min, max) => {
            const num = Number(value);
            if (isNaN(num)) return false;
            if (min !== undefined && num < min) return false;
            if (max !== undefined && num > max) return false;
            return true;
        }
    },
    
    // 错误消息
    messages: {
        required: '此字段为必填项',
        minLength: (min) => `最少需要 ${min} 个字符`,
        maxLength: (max) => `最多允许 ${max} 个字符`,
        phone: '请输入有效的手机号码',
        email: '请输入有效的邮箱地址',
        password: '密码长度应为 6-32 个字符',
        strongPassword: '密码需包含大小写字母和数字，长度至少8位',
        username: '用户名只能包含字母、数字和下划线，长度为 3-20 个字符',
        match: '两次输入不一致',
        number: (min, max) => {
            if (min !== undefined && max !== undefined) {
                return `请输入 ${min} 到 ${max} 之间的数字`;
            } else if (min !== undefined) {
                return `请输入大于等于 ${min} 的数字`;
            } else if (max !== undefined) {
                return `请输入小于等于 ${max} 的数字`;
            }
            return '请输入有效的数字';
        }
    },
    
    /**
     * 验证单个字段
     * @param {any} value - 要验证的值
     * @param {Array} rules - 验证规则数组
     * @returns {Object} - { valid: boolean, message: string }
     */
    validateField: function(value, rules) {
        for (const rule of rules) {
            const ruleName = rule.rule || rule;
            const validator = this.rules[ruleName];
            
            if (!validator) continue;
            
            let isValid = false;
            let message = '';
            
            if (ruleName === 'minLength' || ruleName === 'maxLength') {
                isValid = validator(value, rule.length);
                message = rule.message || this.messages[ruleName](rule.length);
            } else if (ruleName === 'match') {
                isValid = validator(value, rule.compareValue);
                message = rule.message || this.messages[ruleName];
            } else if (ruleName === 'number') {
                isValid = validator(value, rule.min, rule.max);
                message = rule.message || this.messages[ruleName](rule.min, rule.max);
            } else {
                isValid = validator(value);
                message = rule.message || this.messages[ruleName];
            }
            
            if (!isValid) {
                return { valid: false, message };
            }
        }
        return { valid: true, message: '' };
    },
    
    /**
     * 验证整个表单
     * @param {string} formId - 表单ID
     * @param {Object} validationConfig - 验证配置
     * @returns {Object} - { valid: boolean, errors: Object }
     */
    validateForm: function(formId, validationConfig) {
        const errors = {};
        let isValid = true;
        
        for (const [fieldName, config] of Object.entries(validationConfig)) {
            const element = document.querySelector(`#${formId} [name="${fieldName}"]`);
            const value = element ? element.value : '';
            
            const result = this.validateField(value, config.rules);
            
            if (!result.valid) {
                errors[fieldName] = result.message;
                isValid = false;
                
                if (element) {
                    this.showFieldError(element, result.message);
                }
            } else {
                if (element) {
                    this.clearFieldError(element);
                }
            }
        }
        
        return { valid: isValid, errors };
    },
    
    /**
     * 显示字段错误
     */
    showFieldError: function(element, message) {
        this.clearFieldError(element);
        
        element.classList.add('is-invalid');
        
        const formGroup = element.closest('.form-group');
        if (formGroup) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.style.display = 'block';
            errorDiv.textContent = message;
            formGroup.appendChild(errorDiv);
        }
    },
    
    /**
     * 清除字段错误
     */
    clearFieldError: function(element) {
        element.classList.remove('is-invalid');
        
        const formGroup = element.closest('.form-group');
        if (formGroup) {
            const errors = formGroup.querySelectorAll('.invalid-feedback');
            errors.forEach(err => err.remove());
        }
    },
    
    /**
     * 清除表单所有错误
     */
    clearFormErrors: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const elements = form.querySelectorAll('.is-invalid');
        elements.forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        const errors = form.querySelectorAll('.invalid-feedback');
        errors.forEach(err => err.remove());
    },
    
    /**
     * 显示表单级别错误
     */
    showFormError: function(formId, message) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        let alertContainer = form.querySelector('.form-alert');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.className = 'alert alert-danger form-alert';
            alertContainer.setAttribute('role', 'alert');
            form.insertBefore(alertContainer, form.firstChild);
        }
        
        alertContainer.textContent = message;
        alertContainer.style.display = 'block';
    },
    
    /**
     * 清除表单级别错误
     */
    clearFormError: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        const alertContainer = form.querySelector('.form-alert');
        if (alertContainer) {
            alertContainer.style.display = 'none';
        }
    }
};

// ==================== 便捷验证函数 ====================

/**
 * 验证手机号
 */
function validatePhone(phone) {
    return Validator.validateField(phone, ['phone']);
}

/**
 * 验证邮箱
 */
function validateEmail(email) {
    return Validator.validateField(email, ['email']);
}

/**
 * 验证密码
 */
function validatePassword(password, requireStrong = false) {
    return Validator.validateField(password, [requireStrong ? 'strongPassword' : 'password']);
}

/**
 * 验证用户名
 */
function validateUsername(username) {
    return Validator.validateField(username, ['required', 'username']);
}

/**
 * 验证必填
 */
function validateRequired(value) {
    return Validator.validateField(value, ['required']);
}

// 添加CSS动画和样式
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .is-invalid {
            border-color: #dc3545 !important;
        }
        
        .is-invalid:focus {
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
        }
        
        .form-alert {
            margin-bottom: 20px;
        }
    `;
    document.head.appendChild(style);
});
