import axios from 'axios';

const api = axios.create({
    baseURL: '',
    headers: {
        'Content-Type': 'application/json',
    }
});

api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
}, (error) => Promise.reject(error));

api.interceptors.response.use((response) => response, (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/')) {
            window.location.href = '/';
        }
    }
    return Promise.reject(error);
});

export const auth = {
    register: (data: { name: string; email: string; password: string }) =>
        api.post('/api/auth/register', data),
    login: (data: { email: string; password: string }) =>
        api.post('/api/auth/login', data),
    me: () => api.get('/api/auth/me'),
};

export const journal = {
    create: (data: any) => Promise.resolve({ data: { success: true, entry: data } }),
    list: (userId: string) => Promise.resolve({ data: [] }),
};

export const chat = {
    sendMessage: (data: { session_id?: string; message: string }) =>
        api.post('/api/chat/message', data),
    sendMessageStream: async (
        data: {
            session_id?: string;
            message: string;
            face_emotion?: string;
            face_confidence?: number;
        },
        callbacks: {
            onMeta?: (payload: Record<string, unknown>) => void;
            onChunk?: (chunk: string) => void;
            onToken?: (token: string) => void;
            onDone?: (payload: Record<string, unknown>) => void;
            onError?: (error: Error) => void;
        },
    ) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        try {
            const res = await fetch('/api/chat/message/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || `Stream failed: ${res.status}`);
            }
            const reader = res.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const blocks = buffer.split('\n\n');
                buffer = blocks.pop() || '';

                for (const block of blocks) {
                    if (!block.trim()) continue;
                    let eventType = 'message';
                    let dataLine = '';
                    for (const line of block.split('\n')) {
                        if (line.startsWith('event: ')) eventType = line.slice(7).trim();
                        if (line.startsWith('data: ')) dataLine = line.slice(6);
                    }
                    if (!dataLine) continue;
                    const parsed = JSON.parse(dataLine);
                    if (eventType === 'meta') callbacks.onMeta?.(parsed);
                    else if (eventType === 'chunk') callbacks.onChunk?.(parsed.c as string);
                    else if (eventType === 'token') {
                        callbacks.onToken?.(parsed.t as string);
                        callbacks.onChunk?.(parsed.t as string);
                    }
                    else if (eventType === 'done') callbacks.onDone?.(parsed);
                }
            }
        } catch (err) {
            callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
            throw err;
        }
    },
    getHistory: (sessionId: string) => api.get(`/api/chat/session/${sessionId}/history`),
};

export const ai = {
    analyze: (text: string, history: any[] = []) => api.post('/api/ai/analyze/journal', { text, history }),
};

export const avatarApi = {
    speak: (text: string) => api.post('/api/avatar/speak', { text }),
    lipsync: (text: string) => api.post('/api/avatar/lipsync', { text }),
    analyzeFace: (image: string) => api.post('/api/avatar/analyze-face', { image }),
    getFaceStatus: () => api.get('/api/avatar/face-status'),
    fuseEmotion: (data: { text_emotion: string; face_emotion?: string | null; face_confidence?: number }) =>
        api.post('/api/avatar/fuse-emotion', data),
};

export const avatar = {
    respond: (data: any) => api.post('/api/avatar/respond', data),
    ...avatarApi,
};

export const analytics = {
    getDashboard: (userId: string) => Promise.resolve({ data: { entries: [], total: 0 } }),
};

export default api;
