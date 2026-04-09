const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000"; // Local backend for development
// const PROD_API_URL = "https://monitormail-api.onrender.com"; // Production backend


const request = async (endpoint, options) => {
    const token = localStorage.getItem('token');
    const headers = { ...options.headers };
    if (token) {
        headers['x-access-token'] = token;
    }
    // For FormData, let the browser set the Content-Type
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });

    if (!response.ok) {
        let errorData;
        try {
            // Try to parse JSON error first
            errorData = await response.json();
        } catch (e) {
            // If response is not JSON, use status text
  
            errorData = { message: response.statusText || 'An unknown API error occurred.' };
        }
        throw new Error(errorData.message || errorData.error || errorData.reason || 'An API error occurred.');
    }
    
    // Handle potential empty responses (e.g., for DELETE)
    if (response.status === 204) { 
        return null; // Or return an empty object/success message if needed
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        return response.json();
    }
    // Assume blob for file downloads like Excel
    return response.blob(); 
};

// --- AUTH ---
export const login = async (email, password) => {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      
        method: 'POST',
        headers: { 'Authorization': 'Basic ' + btoa(`${email}:${password}`) } // Basic Auth for login
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Login failed.');
    }
    return response.json();
};

// --- WORKFLOW ---
export const uploadPdf = (file) => {
    const formData = new FormData();
    formData.append('file', file);
    // Note: 'Content-Type' header is NOT set here for FormData
    return request('/api/upload-pdf', { method: 'POST', body: formData });
};


export const sortAttendance = (csvData) => request('/api/sort-attendance', {
    method: 'POST',
    // Headers are set automatically by 'request' helper for JSON
    body: JSON.stringify({ csv_data: csvData }),
});

export const fetchStudentDetails = (csvData) => request('/api/fetch-details', {
    method: 'POST',
    body: JSON.stringify({ sorted_csv_data: csvData }),
});

// --- Mass Alert Function ---
export const sendMassAlert = (alertPayload, attachment) => {
    const formData = new FormData();
    formData.append('alert_payload', JSON.stringify(alertPayload));
    if (attachment) {
        formData.append('attachment', attachment);
    }
    return request('/api/alert-all', {
  
        method: 'POST',
        body: formData,
    });
};

// --- EMAIL (for Workflow) ---
export const sendEmails = (emailPayload, attachment) => {
    const formData = new FormData();
    // Append payload as a JSON string
    formData.append('email_payload', JSON.stringify(emailPayload)); 
    if (attachment) {
        formData.append('attachment', attachment);
    }
    // Note: 'Content-Type' header is NOT set here for FormData
    return request('/api/send-emails', {
        method: 'POST',
        body: formData, 
    });
};

export const exportStructuredExcel = (csvData) => request('/api/export-excel-structured', {
    method: 'POST',
    body: JSON.stringify({ sorted_csv_data: csvData }),
});

// --- API Functions for Categories 1, 2 & 3 ---

// Analytics
export const getDashboardAnalytics = () => request('/api/dashboard-analytics', { method: 'GET' });
// Teacher Management (Admin Only)
export const getTeachers = () => request('/api/teachers', { method: 'GET' });

export const saveTeacher = (teacher) => {
    // Determine endpoint and method based on whether it's a new teacher (no id) or existing
    const endpoint = teacher.id ? `/api/teachers/${teacher.id}` : '/api/teachers';
    const method = teacher.id ? 'PUT' : 'POST';
    // Create a copy of the teacher object to potentially remove the password
    const payload = { ...teacher };
    // Only include password if it's being set/changed (not blank)
    if (!payload.password) {
        delete payload.password;
    }
    
    return request(endpoint, {
        method,
        body: JSON.stringify(payload),
    });
};

export const deleteTeacher = (id) => request(`/api/teachers/${id}`, { method: 'DELETE' });

// --- RE-ADDED STUDENT MANAGEMENT FUNCTIONS ---
export const getStudents = (searchQuery = '') => request(`/api/students?search=${encodeURIComponent(searchQuery)}`, { method: 'GET' });

export const saveStudent = (student) => {
    const endpoint = student.id ? `/api/students/${student.id}` : '/api/students';
    const method = student.id ? 'PUT' : 'POST';
    return request(endpoint, {
        method,
        body: JSON.stringify(student),
    });
};

export const deleteStudent = (id) => request(`/api/students/${id}`, { method: 'DELETE' 
});


// --- Template Management ---
export const getTemplates = () => request('/api/templates', { method: 'GET' });

export const saveTemplate = (template) => {
    const endpoint = template.id ? `/api/templates/${template.id}` : '/api/templates';
    const method = template.id ? 'PUT' : 'POST';
    return request(endpoint, {
        method,
        body: JSON.stringify(template),
    });
};

export const deleteTemplate = (id) => request(`/api/templates/${id}`, { method: 'DELETE' 
});

// --- History ---
export const getHistory = (searchQuery = '') => request(`/api/history?search=${encodeURIComponent(searchQuery)}`, { method: 'GET' });

// --- Email Monitoring (Phase 1) ---
export const listMonitors = () => request('/api/monitors', { method: 'GET' });
export const createMonitor = (monitor) => request('/api/monitors', { method: 'POST', body: JSON.stringify(monitor) });
export const deleteMonitor = (id) => request(`/api/monitors/${id}`, { method: 'DELETE' });
export const getMonitorMatches = (id) => request(`/api/monitors/${id}/matches`, { method: 'GET' });

