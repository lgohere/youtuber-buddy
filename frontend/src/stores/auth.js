import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const tokens = ref({
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token')
  })
  const loading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!tokens.value.access)
  const userPlan = computed(() => user.value?.plan || 'free')
  const isPremium = computed(() => user.value?.is_premium || false)

  // Actions
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await api.post('/auth/login/', credentials)
      const { user: userData, tokens: tokenData } = response.data
      
      user.value = userData
      tokens.value = tokenData
      
      // Store tokens in localStorage
      localStorage.setItem('access_token', tokenData.access)
      localStorage.setItem('refresh_token', tokenData.refresh)
      
      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access}`
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erro no login' 
      }
    } finally {
      loading.value = false
    }
  }

  const register = async (userData) => {
    loading.value = true
    try {
      const response = await api.post('/auth/register/', userData)
      const { user: newUser, tokens: tokenData } = response.data
      
      user.value = newUser
      tokens.value = tokenData
      
      // Store tokens in localStorage
      localStorage.setItem('access_token', tokenData.access)
      localStorage.setItem('refresh_token', tokenData.refresh)
      
      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access}`
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || 'Erro no registro' 
      }
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      if (tokens.value.refresh) {
        await api.post('/auth/logout/', { refresh: tokens.value.refresh })
      }
    } catch (error) {
      console.error('Erro no logout:', error)
    } finally {
      // Clear state
      user.value = null
      tokens.value = { access: null, refresh: null }
      
      // Clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      
      // Clear authorization header
      delete api.defaults.headers.common['Authorization']
    }
  }

  const fetchProfile = async () => {
    try {
      const response = await api.get('/auth/profile/')
      user.value = response.data
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erro ao carregar perfil' 
      }
    }
  }

  const updateProfile = async (profileData) => {
    loading.value = true
    try {
      const response = await api.patch('/auth/profile/', profileData)
      user.value = response.data
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data || 'Erro ao atualizar perfil' 
      }
    } finally {
      loading.value = false
    }
  }

  const changePassword = async (passwordData) => {
    loading.value = true
    try {
      await api.post('/auth/change-password/', passwordData)
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Erro ao alterar senha' 
      }
    } finally {
      loading.value = false
    }
  }

  const fetchUserStats = async () => {
    try {
      const response = await api.get('/auth/stats/')
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Erro ao carregar estatísticas' 
      }
    }
  }

  const refreshToken = async () => {
    try {
      if (!tokens.value.refresh) {
        throw new Error('No refresh token available')
      }
      
      const response = await api.post('/auth/token/refresh/', {
        refresh: tokens.value.refresh
      })
      
      tokens.value.access = response.data.access
      localStorage.setItem('access_token', response.data.access)
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`
      
      return { success: true }
    } catch (error) {
      // If refresh fails, logout user
      await logout()
      return { success: false }
    }
  }

  // Initialize auth state
  const initializeAuth = async () => {
    if (tokens.value.access) {
      api.defaults.headers.common['Authorization'] = `Bearer ${tokens.value.access}`
      const result = await fetchProfile()
      if (result.success) {
        return
      }
    }
    
    // Auto-login for development
    if (import.meta.env.DEV) {
      console.log('Auto-login for development...')
      const result = await login({
        email: 'gouartstore@gmail.com',
        password: 'admin123'
      })
      if (result.success) {
        console.log('Auto-login successful')
      } else {
        console.error('Auto-login failed:', result.error)
      }
    }
  }

  return {
    // State
    user,
    tokens,
    loading,
    
    // Getters
    isAuthenticated,
    userPlan,
    isPremium,
    
    // Actions
    login,
    register,
    logout,
    fetchProfile,
    updateProfile,
    changePassword,
    fetchUserStats,
    refreshToken,
    initializeAuth
  }
}) 