import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(() => localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (token) {
            // Verify token and get user info
            api.getMe(token)
                .then(userData => {
                    setUser(userData)
                })
                .catch(() => {
                    // Token invalid, clear it
                    localStorage.removeItem('token')
                    setToken(null)
                })
                .finally(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [token])

    const login = async (email, password) => {
        const result = await api.login(email, password)
        if (result.success && result.token) {
            localStorage.setItem('token', result.token)
            setToken(result.token)
            setUser(result.user)
            return { success: true }
        }
        return { success: false, error: result.error || 'فشل تسجيل الدخول' }
    }

    const register = async (email, name, password) => {
        const result = await api.register(email, name, password)
        if (result.success && result.token) {
            localStorage.setItem('token', result.token)
            setToken(result.token)
            setUser(result.user)
            return { success: true }
        }
        return { success: false, error: result.error || 'فشل إنشاء الحساب' }
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    const value = {
        user,
        token,
        loading,
        login,
        register,
        logout
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
