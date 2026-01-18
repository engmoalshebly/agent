import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import './ChatPage.css'

// Stage names in Arabic
const STAGE_NAMES = {
    greeting: 'الترحيب',
    selecting_service: 'اختيار الخدمة',
    collecting_profile: 'البيانات الشخصية',
    confirming_profile: 'تأكيد البيانات',
    collecting_vehicle: 'بيانات السيارة',
    confirming_vehicle: 'تأكيد السيارة',
    showing_offers: 'عرض العروض',
    selecting_offer: 'اختيار العرض',
    order_summary: 'ملخص الطلب',
    final_confirmation: 'التأكيد النهائي',
    invoice_issued: 'الفاتورة',
    payment_done: 'تم الدفع ✓'
}

function ChatPage() {
    const { user, token, logout } = useAuth()
    const { conversationId: urlConversationId } = useParams()
    const navigate = useNavigate()

    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [conversationId, setConversationId] = useState(urlConversationId || null)
    const [currentStage, setCurrentStage] = useState(null)
    const [loading, setLoading] = useState(false)
    const [sidebarOpen, setSidebarOpen] = useState(true)

    // قائمة المحادثات السابقة
    const [conversations, setConversations] = useState([])
    const [loadingConversations, setLoadingConversations] = useState(false)
    const [activeConvId, setActiveConvId] = useState(urlConversationId || null)

    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // جلب المحادثات السابقة عند التحميل
    useEffect(() => {
        loadConversations()
    }, [token])

    // تحميل المحادثة من URL عند التحميل الأولي
    useEffect(() => {
        if (urlConversationId && token && !messages.length) {
            loadConversation(urlConversationId)
        }
    }, [urlConversationId, token])

    // Focus on input after loading
    useEffect(() => {
        if (!loading && inputRef.current) {
            inputRef.current.focus()
        }
    }, [loading])

    const loadConversations = async () => {
        if (!token) return

        setLoadingConversations(true)
        try {
            const result = await api.getConversations(token)
            if (result.success && result.conversations) {
                setConversations(result.conversations)
            }
        } catch (error) {
            console.error('Error loading conversations:', error)
        } finally {
            setLoadingConversations(false)
        }
    }

    // تحديث صامت في الخلفية بدون تأثير على UI
    const silentLoadConversations = async () => {
        if (!token) return
        try {
            const result = await api.getConversations(token)
            if (result.success && result.conversations) {
                setConversations(result.conversations)
            }
        } catch (error) {
            console.error('Error loading conversations:', error)
        }
    }

    const loadConversation = async (convId) => {
        if (!token || convId === activeConvId) return

        setLoading(true)
        setActiveConvId(convId)
        try {
            const result = await api.getConversationMessages(convId, token)
            if (result.success && result.messages) {
                setMessages(result.messages)
                setConversationId(convId)
                setCurrentStage(result.stage || 'greeting')
                // تحديث URL
                navigate(`/chat/${convId}`, { replace: true })
            }
        } catch (error) {
            console.error('Error loading conversation:', error)
        } finally {
            setLoading(false)
        }
    }

    const sendMessage = async (messageText) => {
        if (!messageText.trim() || loading) return

        const userMessage = { role: 'user', content: messageText }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            const result = await api.sendMessage(messageText, conversationId, token)

            if (result.success) {
                if (result.conversation_id) {
                    setConversationId(result.conversation_id)
                    setActiveConvId(result.conversation_id)
                    // تحديث URL عند إنشاء محادثة جديدة
                    if (!conversationId) {
                        navigate(`/chat/${result.conversation_id}`, { replace: true })
                    }
                }
                if (result.stage) {
                    setCurrentStage(result.stage)
                }

                const assistantMessage = {
                    role: 'assistant',
                    content: result.message || 'لا يوجد رد',
                    has_attachments: result.has_attachments || false,
                    attachments: result.has_attachments ? result.attachments : []
                }
                setMessages(prev => [...prev, assistantMessage])

                // تحديث قائمة المحادثات في الخلفية (صامت)
                setTimeout(() => silentLoadConversations(), 500)
            } else {
                const errorMessage = {
                    role: 'assistant',
                    content: `❌ ${result.error || 'حدث خطأ'}`
                }
                setMessages(prev => [...prev, errorMessage])
            }
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: '❌ تعذر الاتصال بالخادم'
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        sendMessage(input)
    }

    const handleNewConversation = async () => {
        if (conversationId) {
            await api.resetConversation(conversationId, token)
        }
        setMessages([])
        setConversationId(null)
        setActiveConvId(null)
        setCurrentStage(null)
        // العودة للصفحة الرئيسية
        navigate('/', { replace: true })
    }

    const formatTime = (dateStr) => {
        if (!dateStr) return ''
        try {
            const date = new Date(dateStr)
            const now = new Date()
            const diff = now - date

            if (diff < 60000) return 'الآن'
            if (diff < 3600000) return `${Math.floor(diff / 60000)}د`
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}س`
            return date.toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' })
        } catch {
            return ''
        }
    }

    return (
        <div className="chat-app">
            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
                <div className="sidebar-header">
                    <button className="new-chat-btn" onClick={handleNewConversation}>
                        <span className="icon">+</span>
                        <span className="text">محادثة جديدة</span>
                    </button>
                    <button className="toggle-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
                        ☰
                    </button>
                </div>

                <div className="conversations-container">
                    {loadingConversations ? (
                        <div className="loading-state">
                            <div className="spinner"></div>
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="empty-state">
                            <p>لا توجد محادثات</p>
                        </div>
                    ) : (
                        <div className="conversations-list">
                            {conversations.map((conv) => (
                                <div
                                    key={conv.id}
                                    className={`conversation-item ${conv.id === activeConvId ? 'active' : ''}`}
                                    onClick={() => loadConversation(conv.id)}
                                >
                                    <span className="conv-icon">💬</span>
                                    <span className="conv-title">
                                        {STAGE_NAMES[conv.stage] || conv.stage}
                                    </span>
                                    <span className="conv-time">{formatTime(conv.updated_at)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="sidebar-footer">
                    <div className="user-menu">
                        <span className="user-avatar">👤</span>
                        <span className="user-name">{user?.name || 'مستخدم'}</span>
                        <button className="logout-btn" onClick={logout}>خروج</button>
                    </div>
                </div>
            </aside>

            {/* Main Chat Area */}
            <main className="chat-main">
                {/* Header */}
                <header className="chat-header">
                    <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
                        ☰
                    </button>
                    <div className="header-title">
                        <img src="/logo.png" alt="SAIA" className="header-logo" />
                        {currentStage && (
                            <span className="stage-indicator">
                                {STAGE_NAMES[currentStage] || currentStage}
                            </span>
                        )}
                    </div>
                </header>

                {/* Messages Area */}
                <div className="messages-area">
                    {messages.length === 0 ? (
                        <div className="welcome-screen">
                            <img src="/logo.png" alt="SAIA" className="welcome-logo-img" />
                            <h1>SAIA Insurance</h1>
                            <p>المساعد الذكي لكونكورد للتأمين</p>
                            <div className="quick-actions">
                                <button onClick={() => sendMessage('السلام عليكم')}>
                                    👋 ابدأ المحادثة
                                </button>
                                <button onClick={() => sendMessage('أريد تأمين سيارة')}>
                                    🚗 تأمين سيارة
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="messages-scroll">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`message ${msg.role}`}>
                                    <div className="message-avatar">
                                        {msg.role === 'user' ? '👤' : '🤖'}
                                    </div>
                                    <div className="message-content">
                                        <div className="message-text">
                                            {msg.content.split('\n').map((line, i) => (
                                                <p key={i}>{line || '\u00A0'}</p>
                                            ))}
                                        </div>
                                        {msg.has_attachments === true && msg.attachments && msg.attachments.length > 0 && (
                                            <div className="attachments">
                                                {msg.attachments.map((attach, i) => (
                                                    <a
                                                        key={i}
                                                        href={attach.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className={`attachment-link ${attach.type}`}
                                                    >
                                                        {attach.name}
                                                    </a>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="message assistant">
                                    <div className="message-avatar">🤖</div>
                                    <div className="message-content">
                                        <div className="typing-indicator">
                                            <span></span><span></span><span></span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="input-area">
                    <form className="input-form" onSubmit={handleSubmit}>
                        <input
                            ref={inputRef}
                            type="text"
                            className="message-input"
                            placeholder="اكتب رسالتك..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={loading || !input.trim()}
                        >
                            ➤
                        </button>
                    </form>
                    <p className="disclaimer">SAIA - المساعد الذكي لكونكورد للتأمين</p>
                </div>
            </main>
        </div>
    )
}

export default ChatPage
