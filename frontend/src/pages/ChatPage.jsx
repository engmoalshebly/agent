import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import './ChatPage.css'

// Stage names in Arabic
const STAGE_NAMES = {
    greeting: 'الترحيب',
    collecting_profile: 'جمع البيانات',
    collecting_vehicle: 'بيانات السيارة',
    ask_another_vehicle: 'إضافة سيارة',
    showing_offers: 'عرض العروض',
    awaiting_selection: 'اختيار العرض',
    confirmation: 'التأكيد',
    creating_invoice: 'إنشاء الفاتورة',
    pending_payment: 'انتظار الدفع',
    issuing_policy: 'إصدار الوثيقة',
    done: 'تم ✓'
}

function ChatPage() {
    const { user, token, logout } = useAuth()
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [conversationId, setConversationId] = useState(null)
    const [currentStage, setCurrentStage] = useState(null)
    const [loading, setLoading] = useState(false)
    const [sidebarOpen, setSidebarOpen] = useState(true)
    const [showTestData, setShowTestData] = useState(false)
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

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
                }
                if (result.stage) {
                    setCurrentStage(result.stage)
                }

                const assistantMessage = {
                    role: 'assistant',
                    content: result.message || 'لا يوجد رد'
                }
                setMessages(prev => [...prev, assistantMessage])
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

    const handleQuickReply = (text) => {
        sendMessage(text)
    }

    const handleNewConversation = async () => {
        if (conversationId) {
            await api.resetConversation(conversationId, token)
        }
        setMessages([])
        setConversationId(null)
        setCurrentStage(null)
    }

    return (
        <div className="chat-page">
            {/* Header */}
            <header className="chat-header">
                <div className="header-start">
                    <button
                        className="menu-btn"
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                    >
                        ☰
                    </button>
                    <div className="brand">
                        <img src="/logo.png" alt="SAIA" className="brand-logo" />
                    </div>
                </div>

                <div className="header-center">
                    {currentStage && (
                        <div className="stage-badge">
                            📍 {STAGE_NAMES[currentStage] || currentStage}
                        </div>
                    )}
                </div>

                <div className="header-end">
                    <button
                        className="btn btn-secondary test-data-btn"
                        onClick={() => setShowTestData(!showTestData)}
                        title="بيانات تجريبية"
                    >
                        📋
                    </button>
                    <div className="user-info">
                        <span className="user-name">{user?.name || 'مستخدم'}</span>
                    </div>
                    <button className="btn btn-secondary logout-btn" onClick={logout}>
                        خروج
                    </button>
                </div>
            </header>

            <div className="chat-layout">
                {/* Sidebar - Simplified */}
                <aside className={`chat-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
                    <div className="sidebar-section">
                        <h3>⚙️ الإعدادات</h3>

                        {conversationId && (
                            <div className="info-box">
                                <label>🔗 معرف المحادثة</label>
                                <code>{conversationId}</code>
                            </div>
                        )}

                        <button
                            className="btn btn-accent btn-full"
                            onClick={handleNewConversation}
                        >
                            🔄 بدء محادثة جديدة
                        </button>
                    </div>
                </aside>

                {/* Chat Area */}
                <main className="chat-main">
                    <div className="messages-container">
                        {messages.length === 0 ? (
                            <div className="welcome-message animate-fade-in">
                                <div className="welcome-icon">👋</div>
                                <h2>مرحباً بك!</h2>
                                <p>اكتب <strong>"السلام عليكم"</strong> أو أي رسالة لبدء المحادثة</p>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => handleQuickReply('السلام عليكم')}
                                    disabled={loading}
                                >
                                    🚀 بدء المحادثة
                                </button>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg, idx) => (
                                    <div
                                        key={idx}
                                        className={`message ${msg.role} animate-fade-in`}
                                    >
                                        <div className="message-avatar">
                                            {msg.role === 'user' ? '👤' : '🤖'}
                                        </div>
                                        <div className="message-content">
                                            <div className="message-bubble">
                                                {msg.content.split('\n').map((line, i) => (
                                                    <p key={i}>{line}</p>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {loading && (
                                    <div className="message assistant animate-fade-in">
                                        <div className="message-avatar">🤖</div>
                                        <div className="message-content">
                                            <div className="message-bubble typing">
                                                <span></span>
                                                <span></span>
                                                <span></span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Input Area */}
                    <form className="chat-input-area" onSubmit={handleSubmit}>
                        <input
                            type="text"
                            className="chat-input"
                            placeholder="اكتب رسالتك هنا..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            className="send-btn"
                            disabled={loading || !input.trim()}
                        >
                            {loading ? '...' : '📤'}
                        </button>
                    </form>
                </main>
            </div>

            {/* Test Data Modal */}
            {showTestData && (
                <div className="modal-overlay" onClick={() => setShowTestData(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>📋 بيانات تجريبية</h3>
                            <button className="modal-close" onClick={() => setShowTestData(false)}>×</button>
                        </div>
                        <div className="modal-body test-data">
                            <code>الهوية: 1122334455</code>
                            <code>الميلاد: 1990/03/25</code>
                            <code>الجوال: 0501234567</code>
                            <code>اللوحة: س ك ر 5678</code>
                            <code>السيارة: هيونداي سوناتا 2021</code>
                            <code>القيمة: 85000</code>
                        </div>
                    </div>
                </div>
            )}

            {/* Footer */}
            <footer className="chat-footer">
                🛡️ SAIA Insurance Broker Platform v2.0 | Powered by React + FastAPI
            </footer>
        </div>
    )
}

export default ChatPage
