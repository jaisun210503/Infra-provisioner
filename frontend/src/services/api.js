import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(`${API_BASE}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    localStorage.setItem('token', response.data.access_token);
    return response.data;
  },

  async register(email, username, password) {
    const response = await api.post('/auth/register', { email, username, password });
    return response.data;
  },

  async getMe() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

export const userService = {
  async submitRequest(name, resourceType, config) {
    const response = await api.post('/users/requests/submit', {
      name,
      resource_type: resourceType,
      config,
    });
    return response.data;
  },

  async getMyRequests() {
    const response = await api.get('/users/requests');
    return response.data;
  },

  async getMyRequest(id) {
    const response = await api.get(`/users/requests/${id}`);
    return response.data;
  },
};

export const adminService = {
  async getAllRequests(statusFilter = null) {
    let url = '/admin/requests';
    if (statusFilter) {
      url += `?status_filter=${statusFilter}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  async getRequest(id) {
    const response = await api.get(`/admin/requests/${id}`);
    return response.data;
  },

  async approveRequest(id, adminNotes = '') {
    const response = await api.put(`/admin/requests/${id}/approve`, {
      admin_notes: adminNotes,
    });
    return response.data;
  },

  async rejectRequest(id, adminNotes) {
    const response = await api.put(`/admin/requests/${id}/reject`, {
      admin_notes: adminNotes,
    });
    return response.data;
  },

  async getTeams() {
    const response = await api.get('/admin/teams');
    return response.data;
  },

  async createTeam(name, description) {
    const response = await api.post('/admin/teams', { name, description });
    return response.data;
  },

  async addTeamMember(teamId, userId) {
    const response = await api.post(`/admin/teams/${teamId}/members`, {
      user_id: userId,
    });
    return response.data;
  },
};

export default api;
