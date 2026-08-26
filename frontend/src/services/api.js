const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function getToken() {
  return localStorage.getItem('attrition_token');
}

export function setToken(token) {
  localStorage.setItem('attrition_token', token);
}

export function clearToken() {
  localStorage.removeItem('attrition_token');
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Request failed');
  }
  if (options.raw) return response;
  return response.json();
}

export const api = {
  login: (email, password) => request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  dashboard: () => request('/dashboard'),
  employees: (search = '') => request(`/employees${search ? `?search=${encodeURIComponent(search)}` : ''}`),
  addEmployee: (employee) => request('/employees', { method: 'POST', body: JSON.stringify(employee) }),
  updateEmployee: (id, employee) => request(`/employees/${id}`, { method: 'PUT', body: JSON.stringify(employee) }),
  deleteEmployee: (id) => request(`/employees/${id}`, { method: 'DELETE' }),
  uploadEmployees: (formData) => request('/employees/upload', { method: 'POST', body: formData }),
  predict: (id) => request(`/predict/${id}`, { method: 'POST' }),
  analytics: () => request('/analytics'),
  reportUrl: (kind) => `${API_BASE_URL}/reports/${kind}`,
};
