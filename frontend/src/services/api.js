import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env?.DEV
    ? 'http://localhost:8000/api'
    : import.meta.env?.VITE_API_URL || 'https://api.texts.com.br',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(
            `${api.defaults.baseURL}/auth/token/refresh/`,
            { refresh: refreshToken }
          )

          const { access } = response.data
          localStorage.setItem('access_token', access)
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          originalRequest.headers.Authorization = `Bearer ${access}`

          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        delete api.defaults.headers.common['Authorization']
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    if (error.response?.status >= 500) {
      toast.error('Erro interno do servidor. Tente novamente mais tarde.')
    } else if (error.response?.status === 403) {
      toast.error('Acesso negado. Você não tem permissão para esta ação.')
    } else if (error.response?.status === 404) {
      toast.error('Recurso não encontrado.')
    } else if (error.code === 'NETWORK_ERROR') {
      toast.error('Erro de conexão. Verifique sua internet.')
    }

    return Promise.reject(error)
  }
)

export default api 