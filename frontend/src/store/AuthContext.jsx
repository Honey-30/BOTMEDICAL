import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiService } from '../services/api'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        apiService.setAuthToken(token)
        const userData = await apiService.getCurrentUser()
        setUser(userData)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('auth_token')
    } finally {
      setLoading(false)
    }
  }

  const login = async (credentials) => {
    try {
      const response = await apiService.login(credentials)
      const { access_token, user: userData } = response
      
      localStorage.setItem('auth_token', access_token)
      apiService.setAuthToken(access_token)
      setUser(userData)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await apiService.register(userData)
      const { access_token, user: newUser } = response
      
      localStorage.setItem('auth_token', access_token)
      apiService.setAuthToken(access_token)
      setUser(newUser)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    apiService.setAuthToken(null)
    setUser(null)
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}