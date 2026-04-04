import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error.response?.data?.detail || error.message);
  }
);

export default api;
