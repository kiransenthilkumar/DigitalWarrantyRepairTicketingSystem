// Main JavaScript for Warranty System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize popovers
    initializePopovers();
    
    // Handle alerts auto-dismiss
    handleAutoCloseAlerts();
    
    // Handle form validation
    handleFormValidation();
});

/* Tooltips Initialization */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* Popovers Initialization */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/* Auto-dismiss alerts after 5 seconds */
function handleAutoCloseAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Skip alerts with specific classes that shouldn't auto-close
        if (!alert.classList.contains('alert-persistent')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

/* Form Validation */
function handleFormValidation() {
    const forms = document.querySelectorAll('form:not([novalidate])');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/* Utility: Format currency */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(value);
}

/* Utility: Format date */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/* Utility: Show loading spinner */
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-primary';
    spinner.role = 'status';
    spinner.innerHTML = '<span class="visually-hidden">Loading...</span>';
    return spinner;
}

/* Utility: Confirm delete action */
function confirmAction(message = 'Are you sure you want to proceed?') {
    return confirm(message);
}

/* Export data to CSV */
function exportToCSV(filename, data) {
    const csv = convertToCSV(data);
    downloadCSV(csv, filename);
}

function convertToCSV(objArray) {
    const array = typeof objArray !== 'object' ? JSON.parse(objArray) : objArray;
    let str = '';
    
    for (let i = 0; i < array.length; i++) {
        let line = '';
        for (let index in array[i]) {
            if (line !== '') line += ',';
            line += '"' + array[i][index] + '"';
        }
        str += line + '\r\n';
    }
    return str;
}

function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.download = filename;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/* Print functionality */
function printPage() {
    window.print();
}

/* Search functionality with debounce */
function setupSearch(inputSelector, functionToCall) {
    let timeout;
    const searchInput = document.querySelector(inputSelector);
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                functionToCall(this.value);
            }, 300);
        });
    }
}

/* API Call with error handling */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Call Error:', error);
        showAlert('An error occurred. Please try again.', 'danger');
        return null;
    }
}

/* Show custom alert */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto retire alert
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

/* Dark Mode Toggle (Optional) */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Load dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}
