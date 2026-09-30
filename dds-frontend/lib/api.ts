import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';
import { redirectToLogin, refreshAccessToken } from '@/lib/apiFetch';

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
      // Shared with the chat stream path so the 1 hour access token expiry is
      // handled the same way everywhere.
      const accessToken = await refreshAccessToken();
      if (accessToken && error.config) {
        error.config.headers.Authorization = `Bearer ${accessToken}`;
        return api(error.config);
      }
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);

export default api;
