import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const api = axios.create({
  baseURL: '/api/',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined') {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      const store = useAuthStore.getState();
      if (store.refreshToken) {
        try {
          const res = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refreshToken: store.refreshToken }),
          });
          if (res.ok) {
            const data = await res.json();
            store.setTokens(data.accessToken, data.refreshToken);
            if (error.config) {
              error.config.headers.Authorization = `Bearer ${data.accessToken}`;
              return api(error.config);
            }
          }
        } catch {
          store.logout();
        }
      } else {
        store.logout();
      }
    }
    return Promise.reject(error);
  }
);

export default api;
