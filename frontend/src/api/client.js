import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const register = (data) => api.post('/auth/register', data)
export const login = (data) => api.post('/auth/login', data)
export const getMe = () => api.get('/users/me')

// ── Projects ──────────────────────────────────────────────────────────────────
export const getProjects = () => api.get('/projects')
export const createProject = (data) => api.post('/projects', data)
export const updateProject = (id, data) => api.patch(`/projects/${id}`, data)
export const deleteProject = (id) => api.delete(`/projects/${id}`)

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const getTasks = (projectId, params) => api.get(`/projects/${projectId}/tasks`, { params })
export const createTask = (projectId, data) => api.post(`/projects/${projectId}/tasks`, data)
export const updateTask = (projectId, taskId, data) => api.patch(`/projects/${projectId}/tasks/${taskId}`, data)
export const deleteTask = (projectId, taskId) => api.delete(`/projects/${projectId}/tasks/${taskId}`)

// ── AI ────────────────────────────────────────────────────────────────────────
export const getSuggestions = (projectId) => api.get(`/ai/projects/${projectId}/suggest-priorities`)
export const applySuggestions = (projectId) => api.post(`/ai/projects/${projectId}/apply-suggestions`)

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getMyAnalytics = () => api.get('/analytics/me')
export const getProjectAnalytics = (projectId) => api.get(`/analytics/projects/${projectId}`)
