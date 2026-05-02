/*
 * 自动售货机管理系统 - 通用JavaScript工具
 */

/**
 * 显示Toast提示
 * @param {string} title - 提示标题
 * @param {string} message - 提示内容
 * @param {string} type - 提示类型 (success, error, warning, info)
 */
function showToast(title, message, type = 'info') {
    const toast = $('#toast');
    const toastTitle = $('#toastTitle');
    const toastBody = $('#toastBody');
    
    // 设置标题
    toastTitle.text(title);
    
    // 设置内容
    toastBody.text(message);
    
    // 设置样式
    toast.removeClass('bg-success bg-danger bg-warning bg-info');
    const titleEl = toast.find('.toast-header strong');
    titleEl.removeClass('text-white text-dark');
    
    switch(type) {
        case 'success':
            toast.addClass('bg-success');
            titleEl.addClass('text-white');
            toastTitle.text(title || '成功');
            break;
        case 'error':
            toast.addClass('bg-danger');
            titleEl.addClass('text-white');
            toastTitle.text(title || '错误');
            break;
        case 'warning':
            toast.addClass('bg-warning');
            titleEl.addClass('text-dark');
            toastTitle.text(title || '警告');
            break;
        case 'info':
        default:
            toast.addClass('bg-info');
            titleEl.addClass('text-white');
            toastTitle.text(title || '提示');
            break;
    }
    
    // 显示Toast
    toast.toast('show');
}

/**
 * 初始化测试数据
 */
function initTestData() {
    // 创建确认对话框
    const confirmed = confirm(
        '⚠️ 重要提示：\n\n' +
        '此操作将：\n' +
        '1. 重置当前数据库\n' +
        '2. 删除所有现有数据\n' +
        '3. 生成新的测试数据\n\n' +
        '确定要继续吗？'
    );
    
    if (!confirmed) {
        return;
    }
    
    // 显示进度提示
    showToast('信息', '正在初始化测试数据，请稍候...', 'info');
    
    // 显示加载中的全屏覆盖层
    const overlay = $(`
        <div id="initOverlay" class="fixed-top fixed-bottom bg-dark bg-opacity-75 d-flex align-items-center justify-content-center" style="z-index: 99999;">
            <div class="text-center text-white">
                <div class="spinner-border mb-3" style="width: 3rem; height: 3rem;" role="status">
                    <span class="sr-only">加载中...</span>
                </div>
                <h4 id="initStatusText">正在初始化测试数据...</h4>
                <p class="text-muted mt-2" id="initProgressText">请稍候，这可能需要几秒钟</p>
            </div>
        </div>
    `).appendTo('body');
    
    // 执行初始化请求
    $.ajax({
        url: '/init-test-data',
        method: 'GET',
        timeout: 60000, // 60秒超时
        success: function(response) {
            if (response.success) {
                // 更新状态
                $('#initStatusText').text('初始化成功！');
                $('#initProgressText').text('即将刷新页面...');
                
                // 显示成功提示
                showToast('成功', response.message, 'success');
                
                // 2秒后刷新页面
                setTimeout(function() {
                    overlay.remove();
                    location.reload();
                }, 2000);
            } else {
                // 显示失败信息
                $('#initStatusText').text('初始化失败');
                $('#initProgressText').text(response.message);
                
                showToast('错误', response.message, 'error');
                
                setTimeout(function() {
                    overlay.remove();
                }, 3000);
            }
        },
        error: function(xhr, status, error) {
            let errorMsg = '初始化失败';
            
            if (status === 'timeout') {
                errorMsg = '请求超时，请重试';
            } else if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            } else if (error) {
                errorMsg = error;
            }
            
            // 显示失败信息
            $('#initStatusText').text('初始化失败');
            $('#initProgressText').text(errorMsg);
            
            showToast('错误', errorMsg, 'error');
            
            setTimeout(function() {
                overlay.remove();
            }, 3000);
        }
    });
}

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期对象或日期字符串
 * @param {string} format - 格式 ('full', 'date', 'time')
 * @returns {string} 格式化后的日期时间字符串
 */
function formatDateTime(date, format = 'full') {
    if (!date) return '-';
    
    let d;
    if (date instanceof Date) {
        d = date;
    } else {
        d = new Date(date);
    }
    
    if (isNaN(d.getTime())) return '-';
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    switch(format) {
        case 'date':
            return `${year}-${month}-${day}`;
        case 'time':
            return `${hours}:${minutes}:${seconds}`;
        case 'full':
        default:
            return `${year}-${month}-${day} ${hours}:${minutes}`;
    }
}

/**
 * 格式化货币
 * @param {number} amount - 金额
 * @param {string} symbol - 货币符号
 * @returns {string} 格式化后的货币字符串
 */
function formatCurrency(amount, symbol = '¥') {
    if (amount === null || amount === undefined) return symbol + '0.00';
    return symbol + parseFloat(amount).toFixed(2);
}

/**
 * 格式化数字
 * @param {number} num - 数字
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的数字字符串
 */
function formatNumber(num, decimals = 0) {
    if (num === null || num === undefined) return '0';
    return parseFloat(num).toLocaleString('zh-CN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要执行的函数
 * @param {number} limit - 时间限制（毫秒）
 * @returns {Function} 节流后的函数
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 获取URL参数
 * @param {string} name - 参数名
 * @returns {string|null} 参数值
 */
function getUrlParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * 设置URL参数
 * @param {string} name - 参数名
 * @param {string} value - 参数值
 */
function setUrlParam(name, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

/**
 * 删除URL参数
 * @param {string} name - 参数名
 */
function deleteUrlParam(name) {
    const url = new URL(window.location.href);
    url.searchParams.delete(name);
    window.history.pushState({}, '', url);
}

/**
 * 深拷贝对象
 * @param {Object} obj - 要拷贝的对象
 * @returns {Object} 拷贝后的对象
 */
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

/**
 * 检查是否为空值
 * @param {*} value - 要检查的值
 * @returns {boolean} 是否为空
 */
function isEmpty(value) {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string' && value.trim() === '') return true;
    if (Array.isArray(value) && value.length === 0) return true;
    if (typeof value === 'object' && Object.keys(value).length === 0) return true;
    return false;
}

/**
 * 生成随机ID
 * @param {number} length - ID长度
 * @returns {string} 随机ID
 */
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * 生成订单号
 * @param {string} prefix - 前缀
 * @returns {string} 订单号
 */
function generateOrderNumber(prefix = 'ORD') {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const random = String(Math.floor(Math.random() * 1000)).padStart(3, '0');
    
    return `${prefix}${year}${month}${day}${hours}${minutes}${seconds}${random}`;
}

// 页面加载完成后初始化
$(document).ready(function() {
    // 初始化Toast
    $('.toast').toast({
        delay: 3000,
        autohide: true
    });
    
    // 为所有模态框添加ESC键关闭支持
    $('.modal').on('shown.bs.modal', function() {
        $(this).attr('tabindex', '-1');
    });
    
    // 表单输入聚焦效果
    $('input, select, textarea').on('focus', function() {
        $(this).closest('.form-group').addClass('focused');
    }).on('blur', function() {
        $(this).closest('.form-group').removeClass('focused');
    });
    
    console.log('自动售货机管理系统 - 通用工具已加载');
});
