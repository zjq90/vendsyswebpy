/**
 * 通用工具函数
 * 处理API请求、认证、提示等
 */

const API_BASE_URL = '';

// 存储token
let authToken = localStorage.getItem('authToken') || '';
let currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');

/**
 * 获取认证头部
 */
function getAuthHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    return headers;
}

/**
 * 通用API请求函数
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: getAuthHeaders(),
        credentials: 'include'
    };
    
    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        // 未授权，清除登录状态并跳转到登录页
        logout();
        window.location.href = '/login';
        throw new Error('登录已过期，请重新登录');
    }
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || '请求失败');
    }
    return data;
}

/**
 * GET请求
 */
async function apiGet(url) {
    return apiRequest(url, { method: 'GET' });
}

/**
 * POST请求
 */
async function apiPost(url, data) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT请求
 */
async function apiPut(url, data) {
    return apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE请求
 */
async function apiDelete(url) {
    return apiRequest(url, { method: 'DELETE' });
}

/**
 * 登录
 */
async function login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || '登录失败');
    }
    
    // 保存登录信息
    authToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    return data;
}

/**
 * 登出
 */
function logout() {
    authToken = '';
    currentUser = {};
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
}

/**
 * 检查登录状态
 */
function isLoggedIn() {
    return !!authToken;
}

/**
 * 检查是否是管理员
 */
function isAdmin() {
    return currentUser.role === 'admin';
}

/**
 * 显示提示消息
 */
function showMessage(message, type = 'success') {
    // 创建消息元素
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? '✓' : '✗';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show fixed-top m-3" role="alert" style="z-index: 9999; max-width: 400px; right: 0;">
            <strong>${icon}</strong> ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        </div>
    `;
    
    $('body').append(alertHtml);
    
    // 自动关闭
    setTimeout(() => {
        $('.alert.fixed-top').alert('close');
    }, 3000);
}

/**
 * 显示确认对话框
 */
function showConfirm(message, onConfirm) {
    const modalId = 'confirmModal_' + Date.now();
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">确认操作</h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary confirm-btn">确认</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(modalHtml);
    const $modal = $(`#${modalId}`);
    
    $modal.find('.confirm-btn').click(() => {
        $modal.modal('hide');
        setTimeout(() => {
            $modal.remove();
            onConfirm();
        }, 200);
    });
    
    $modal.on('hidden.bs.modal', () => {
        setTimeout(() => $modal.remove(), 200);
    });
    
    $modal.modal('show');
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN');
}

/**
 * 获取状态徽章样式
 */
function getStatusBadge(status) {
    const badgeMap = {
        'normal': 'badge-success',
        'online': 'badge-success',
        'active': 'badge-success',
        'success': 'badge-success',
        'maintenance': 'badge-warning',
        'warning': 'badge-warning',
        'fair': 'badge-warning',
        'faulty': 'badge-danger',
        'offline': 'badge-danger',
        'failed': 'badge-danger',
        'inactive': 'badge-secondary',
        'empty': 'badge-secondary',
        'poor': 'badge-secondary',
        'pending': 'badge-info',
        'sent': 'badge-info',
        'testing': 'badge-info',
        'excellent': 'badge-primary',
        'good': 'badge-success',
        'release': 'badge-success'
    };
    return badgeMap[status] || 'badge-secondary';
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
    const textMap = {
        'normal': '正常',
        'online': '在线',
        'active': '启用',
        'success': '成功',
        'maintenance': '维护中',
        'warning': '警告',
        'fair': '一般',
        'faulty': '故障',
        'offline': '离线',
        'failed': '失败',
        'inactive': '禁用',
        'empty': '空',
        'poor': '差',
        'pending': '待执行',
        'sent': '已发送',
        'testing': '测试中',
        'excellent': '优秀',
        'good': '良好',
        'release': '已发布',
        'deprecated': '已废弃'
    };
    return textMap[status] || status;
}

/**
 * 初始化导航栏
 */
function initNavbar() {
    const $navbar = $('#navbar');
    if ($navbar.length === 0) return;
    
    // 设置用户信息
    if (currentUser.real_name) {
        $('#userName').text(currentUser.real_name);
        $('#userRole').text(currentUser.role === 'admin' ? '管理员' : '业务员');
    }
    
    // 根据角色显示/隐藏菜单
    if (!isAdmin()) {
        $('.admin-only').hide();
    }
    
    // 登出按钮
    $('#logoutBtn').click((e) => {
        e.preventDefault();
        logout();
        window.location.href = '/login';
    });
}

/**
 * 页面初始化
 */
$(document).ready(() => {
    // 检查登录状态（登录页面除外）
    const isLoginPage = window.location.pathname === '/login';
    if (!isLoginPage && !isLoggedIn()) {
        window.location.href = '/login';
        return;
    }
    
    // 初始化导航栏
    initNavbar();
});
