import axios from 'axios'

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  setAuthToken(token) {
    if (token) {
      this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete this.api.defaults.headers.common['Authorization']
    }
  }

  // Auth methods
  async login(credentials) {
    const response = await this.api.post('/auth/login', credentials)
    return response.data
  }

  async register(userData) {
    const response = await this.api.post('/auth/register', userData)
    return response.data
  }

  async getCurrentUser() {
    const response = await this.api.get('/auth/me')
    return response.data
  }

  // Project methods
  async getProjects(params = {}) {
    const response = await this.api.get('/projects', { params })
    return response.data
  }

  async getProject(id) {
    const response = await this.api.get(`/projects/${id}`)
    return response.data
  }

  async createProject(projectData) {
    const response = await this.api.post('/projects', projectData)
    return response.data
  }

  async updateProject(id, projectData) {
    const response = await this.api.put(`/projects/${id}`, projectData)
    return response.data
  }

  async deleteProject(id) {
    const response = await this.api.delete(`/projects/${id}`)
    return response.data
  }

  async getProjectMembers(projectId) {
    const response = await this.api.get(`/projects/${projectId}/members`)
    return response.data
  }

  async addProjectMember(projectId, memberData) {
    const response = await this.api.post(`/projects/${projectId}/members`, memberData)
    return response.data
  }

  // Task methods
  async getTasks(params = {}) {
    const response = await this.api.get('/tasks', { params })
    return response.data
  }

  async getTask(id) {
    const response = await this.api.get(`/tasks/${id}`)
    return response.data
  }

  async createTask(taskData) {
    const response = await this.api.post('/tasks', taskData)
    return response.data
  }

  async updateTask(id, taskData) {
    const response = await this.api.put(`/tasks/${id}`, taskData)
    return response.data
  }

  async deleteTask(id) {
    const response = await this.api.delete(`/tasks/${id}`)
    return response.data
  }

  async getTaskComments(taskId) {
    const response = await this.api.get(`/tasks/${taskId}/comments`)
    return response.data
  }

  async addTaskComment(taskId, commentData) {
    const response = await this.api.post(`/tasks/${taskId}/comments`, commentData)
    return response.data
  }

  // AI methods
  async sendChatMessage(messageData) {
    const response = await this.api.post('/ai/chat', messageData)
    return response.data
  }

  async getChatSessions() {
    const response = await this.api.get('/ai/sessions')
    return response.data
  }

  async getChatSession(sessionId) {
    const response = await this.api.get(`/ai/sessions/${sessionId}`)
    return response.data
  }

  async analyzeProject(projectId) {
    const response = await this.api.post(`/ai/analyze-project/${projectId}`)
    return response.data
  }

  async analyzeTasks(projectId = null) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await this.api.post('/ai/analyze-tasks', {}, { params })
    return response.data
  }

  async suggestPriorities(projectId = null) {
    const params = projectId ? { project_id: projectId } : {}
    const response = await this.api.post('/ai/suggest-priorities', {}, { params })
    return response.data
  }

  // Analytics methods
  async getOverviewAnalytics() {
    const response = await this.api.get('/analytics/overview')
    return response.data
  }

  async getProjectAnalytics(projectId) {
    const response = await this.api.get(`/analytics/project/${projectId}/analytics`)
    return response.data
  }

  async getProductivityReport(days = 30) {
    const response = await this.api.get('/analytics/reports/productivity', { 
      params: { days } 
    })
    return response.data
  }

  // User methods
  async getUserProfile() {
    const response = await this.api.get('/users/profile')
    return response.data
  }

  async updateUserProfile(profileData) {
    const response = await this.api.put('/users/profile', profileData)
    return response.data
  }
}

export const apiService = new ApiService()