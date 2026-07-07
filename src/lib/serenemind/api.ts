import axios from "axios";

const CHAT_BASE = "/api/serenemind/chat";
const AVATAR_BASE = "/api/serenemind/avatar";

const api = axios.create({
  baseURL: "",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const path = window.location.pathname;
      if (!path.includes("/login") && path !== "/") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

/** Main-app session (HTTP-only cookie). Not used by SereneMind UI in Phase 2 step 1. */
export const auth = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post("/api/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/login", data),
  me: () => api.get("/api/me"),
};

export const journal = {
  create: (data: unknown) =>
    Promise.resolve({ data: { success: true, entry: data } }),
  list: () => Promise.resolve({ data: [] }),
};

export const chat = {
  sendMessage: (data: { session_id?: string; message: string }) =>
    api.post(`${CHAT_BASE}/message`, data),
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
    try {
      const res = await fetch(`${CHAT_BASE}/message/stream`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || `Stream failed: ${res.status}`);
      }
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          if (!block.trim()) continue;
          let eventType = "message";
          let dataLine = "";
          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) eventType = line.slice(7).trim();
            if (line.startsWith("data: ")) dataLine = line.slice(6);
          }
          if (!dataLine) continue;
          const parsed = JSON.parse(dataLine);
          if (eventType === "meta") callbacks.onMeta?.(parsed);
          else if (eventType === "chunk")
            callbacks.onChunk?.(parsed.c as string);
          else if (eventType === "token") {
            callbacks.onToken?.(parsed.t as string);
            callbacks.onChunk?.(parsed.t as string);
          } else if (eventType === "done") callbacks.onDone?.(parsed);
        }
      }
    } catch (err) {
      callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
      throw err;
    }
  },
  getHistory: (sessionId: string) =>
    api.get(`${CHAT_BASE}/session/${sessionId}/history`),
};

export const ai = {
  analyze: (text: string, history: unknown[] = []) =>
    api.post("/api/ai/analyze/journal", { text, history }),
};

export const avatarApi = {
  speak: (text: string) => api.post(`${AVATAR_BASE}/speak`, { text }),
  lipsync: (text: string) => api.post(`${AVATAR_BASE}/lipsync`, { text }),
  analyzeFace: (image: string) =>
    api.post(`${AVATAR_BASE}/analyze-face`, { image }),
  getFaceStatus: () => api.get(`${AVATAR_BASE}/face-status`),
  fuseEmotion: (data: {
    text_emotion: string;
    face_emotion?: string | null;
    face_confidence?: number;
  }) => api.post(`${AVATAR_BASE}/fuse-emotion`, data),
};

export const avatar = {
  respond: (data: unknown) => api.post(`${AVATAR_BASE}/respond`, data),
  ...avatarApi,
};

export const analytics = {
  getDashboard: () =>
    Promise.resolve({ data: { entries: [], total: 0 } }),
};

export default api;
