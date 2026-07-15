import axios from 'axios';
import { message } from 'antd';

const apiClient = axios.create({
  baseURL: '',
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      // 已在登录页 → 显示错误而不是静默失败
      if (window.location.pathname.startsWith('/login')) {
        message.error(error.response?.data?.detail || '密码错误');
      } else {
        window.location.href = '/login';
      }
    } else {
      message.error(error.response?.data?.detail || error.message || '请求失败');
    }
    return Promise.reject(error);
  },
);

export default apiClient;
