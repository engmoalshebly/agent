/**
 * API Client for SAIA Insurance Broker
 */

// Use environment variable or default to relative path
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`

    // Extract headers from options separately to merge them properly
    const { headers: optionHeaders, ...restOptions } = options

    const config = {
        ...restOptions,
        headers: {
            'Content-Type': 'application/json',
            ...optionHeaders
        }
    }

    try {
        const response = await fetch(url, config)
        const data = await response.json()

        if (!response.ok) {
            // Extract error message properly
            let errorMessage = 'حدث خطأ'
            if (typeof data.detail === 'string') {
                errorMessage = data.detail
            } else if (Array.isArray(data.detail)) {
                // Pydantic validation errors
                errorMessage = data.detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ')
            } else if (typeof data.detail === 'object' && data.detail !== null) {
                errorMessage = data.detail.msg || data.detail.message || JSON.stringify(data.detail)
            } else if (data.message) {
                errorMessage = data.message
            }

            return {
                success: false,
                error: errorMessage,
                status: response.status
            }
        }

        return { success: true, ...data }
    } catch (error) {
        console.error('API Error:', error)
        return {
            success: false,
            error: 'تعذر الاتصال بالخادم'
        }
    }
}

export const api = {
    // Auth endpoints
    login: async (email, password) => {
        return request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        })
    },

    register: async (email, name, password) => {
        return request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, name, password })
        })
    },

    getMe: async (token) => {
        const result = await request('/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        if (result.success) {
            return result
        }
        throw new Error(result.error)
    },

    // Chat endpoints
    sendMessage: async (message, conversationId, token) => {
        const body = { message }
        if (conversationId) {
            body.conversation_id = conversationId
        }
        console.log('🚀 Sending chat request:', { body, token: token ? '✓' : '✗' })
        return request('/chat', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        })
    },

    resetConversation: async (conversationId, token) => {
        return request(`/chat/reset?conversation_id=${conversationId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
    },

    getContext: async (conversationId, token) => {
        return request(`/chat/context/${conversationId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
    },

    // Get user conversations history
    getConversations: async (token) => {
        return request('/conversations', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
    },

    // Get conversation messages
    getConversationMessages: async (conversationId, token) => {
        return request(`/conversations/${conversationId}/messages`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
    }
}

