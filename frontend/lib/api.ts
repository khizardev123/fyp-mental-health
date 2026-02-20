import axios from 'axios';

// Use relative URLs so Next.js rewrites handle routing to the correct microservice
const api = axios.create({
    baseURL: '', // relative — Next.js rewrites in next.config.mjs handle forwarding
    headers: {
        'Content-Type': 'application/json',
    }
});

// Request interceptor to add token
api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
}, (error) => Promise.reject(error));

// Response interceptor for auth errors
api.interceptors.response.use((response) => response, (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
        if (!window.location.pathname.includes('/login')) {
            // Optional: redirect to login
        }
    }
    return Promise.reject(error);
});

export const auth = {
    login: (data: any) => Promise.resolve({ data: { token: 'mock-token', user: { id: '1', email: data.email } } }),
    register: (data: any) => Promise.resolve({ data: { token: 'mock-token', user: { id: '1', email: data.email } } }),
    me: () => Promise.resolve({ data: { user: { id: '1', email: 'guest@serenemind.local' } } }),
};

export const journal = {
    create: (data: any) => Promise.resolve({ data: { success: true, entry: data } }),
    list: (userId: string) => Promise.resolve({ data: [] }),
};

export const ai = {
    analyze: (text: string) => api.post('/api/ai/analyze/journal', { text }),
};

export const avatar = {
    respond: (data: any) => api.post('/api/avatar/respond', data),
};

export const analytics = {
    getDashboard: (userId: string) => Promise.resolve({ data: { entries: [], total: 0 } }),
};

export default api;
