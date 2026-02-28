import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import './LoginPage.css'

function LoginPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [name, setName] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    const { login, register } = useAuth()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        if (!isLogin && password !== confirmPassword) {
            setError('كلمات المرور غير متطابقة')
            setLoading(false)
            return
        }

        try {
            let result
            if (isLogin) {
                result = await login(email, password)
            } else {
                result = await register(email, name, password)
            }

            if (!result.success) {
                setError(result.error)
            }
        } catch (err) {
            setError('حدث خطأ غير متوقع')
        } finally {
            setLoading(false)
        }
    }

    const toggleMode = () => {
        setIsLogin(!isLogin)
        setError('')
        setEmail('')
        setName('')
        setPassword('')
        setConfirmPassword('')
    }

    return (
        <div className="login-page">
            <div className="login-container">
                {/* Logo Section */}
                <div className="login-header">
                    <div className="logo">
                        <img src="./logo-dark.png" alt="SAIA Insurance" className="logo-image" />
                    </div>
                    <p className="tagline">منصة وسيط التأمين الذكي</p>
                </div>

                {/* Form Card */}
                <div className="login-card animate-fade-in">
                    <h2>{isLogin ? 'تسجيل الدخول' : 'إنشاء حساب جديد'}</h2>

                    {error && (
                        <div className="error-message">
                            <span>⚠️</span> {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="input-group">
                            <label htmlFor="email">البريد الإلكتروني</label>
                            <input
                                id="email"
                                type="email"
                                className="input"
                                placeholder="example@email.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={loading}
                            />
                        </div>

                        {!isLogin && (
                            <div className="input-group animate-fade-in">
                                <label htmlFor="name">الاسم الكامل</label>
                                <input
                                    id="name"
                                    type="text"
                                    className="input"
                                    placeholder="أحمد محمد"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required={!isLogin}
                                    disabled={loading}
                                />
                            </div>
                        )}

                        <div className="input-group">
                            <label htmlFor="password">كلمة المرور</label>
                            <input
                                id="password"
                                type="password"
                                className="input"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                                disabled={loading}
                            />
                        </div>

                        {!isLogin && (
                            <div className="input-group animate-fade-in">
                                <label htmlFor="confirmPassword">تأكيد كلمة المرور</label>
                                <input
                                    id="confirmPassword"
                                    type="password"
                                    className="input"
                                    placeholder="••••••••"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required={!isLogin}
                                    minLength={6}
                                    disabled={loading}
                                />
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn btn-primary btn-full"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="btn-spinner"></span>
                                    جاري المعالجة...
                                </>
                            ) : (
                                isLogin ? 'تسجيل الدخول' : 'إنشاء الحساب'
                            )}
                        </button>
                    </form>

                    <div className="toggle-mode">
                        <span>{isLogin ? 'ليس لديك حساب؟' : 'لديك حساب بالفعل؟'}</span>
                        <button
                            type="button"
                            className="toggle-btn"
                            onClick={toggleMode}
                            disabled={loading}
                        >
                            {isLogin ? 'سجل الآن' : 'سجل دخولك'}
                        </button>
                    </div>
                </div>

                {/* Footer */}
                <div className="login-footer">
                    <p>🛡️ SAIA Insurance Broker Platform v2.0</p>
                </div>
            </div>

            {/* Background decoration */}
            <div className="bg-decoration">
                <div className="circle circle-1"></div>
                <div className="circle circle-2"></div>
                <div className="circle circle-3"></div>
            </div>
        </div>
    )
}

export default LoginPage
