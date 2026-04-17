import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Auth.css';

function Auth() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(loginForm),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Ошибка входа');
      }
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(registerForm),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Ошибка регистрации');
      }
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    window.location.href = `${import.meta.env.VITE_API_URL}/api/v1/user/google/url`;
  };

  const handleYandex = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/yandex/query_params`);
      const params = await res.json();
      const query = new URLSearchParams(params);
      window.location.href = `https://oauth.yandex.ru/authorize?${query}`;
    } catch (err) {
      setError('Не удалось подключиться к Яндексу');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-noise" />

      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">▲</div>
          <h1 className="auth-title">
            {mode === 'login' ? 'Вход' : 'Регистрация'}
          </h1>
          <p className="auth-subtitle">
            {mode === 'login' ? 'Рады видеть вас снова' : 'Создайте аккаунт'}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null); }}
          >
            Вход
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null); }}
          >
            Регистрация
          </button>
          <div className={`auth-tab-indicator ${mode === 'register' ? 'right' : ''}`} />
        </div>

        {error && (
          <div className="auth-error-box">
            <span className="auth-error-icon">!</span>
            {error}
          </div>
        )}

        {mode === 'login' ? (
          <form className="auth-form" onSubmit={handleLogin}>
            <div className="auth-field">
              <label className="auth-label">Email</label>
              <input
                className="auth-input"
                type="email"
                placeholder="you@example.com"
                value={loginForm.email}
                onChange={e => setLoginForm({ ...loginForm, email: e.target.value })}
                required
              />
            </div>
            <div className="auth-field">
              <label className="auth-label">Пароль</label>
              <input
                className="auth-input"
                type="password"
                placeholder="••••••••"
                value={loginForm.password}
                onChange={e => setLoginForm({ ...loginForm, password: e.target.value })}
                required
              />
            </div>
            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? <span className="auth-spinner" /> : 'Войти'}
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegister}>
            <div className="auth-field">
              <label className="auth-label">Имя пользователя</label>
              <input
                className="auth-input"
                type="text"
                placeholder="username"
                value={registerForm.username}
                onChange={e => setRegisterForm({ ...registerForm, username: e.target.value })}
                required
              />
            </div>
            <div className="auth-field">
              <label className="auth-label">Email</label>
              <input
                className="auth-input"
                type="email"
                placeholder="you@example.com"
                value={registerForm.email}
                onChange={e => setRegisterForm({ ...registerForm, email: e.target.value })}
                required
              />
            </div>
            <div className="auth-field">
              <label className="auth-label">Пароль</label>
              <input
                className="auth-input"
                type="password"
                placeholder="••••••••"
                value={registerForm.password}
                onChange={e => setRegisterForm({ ...registerForm, password: e.target.value })}
                required
              />
            </div>
            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? <span className="auth-spinner" /> : 'Создать аккаунт'}
            </button>
          </form>
        )}

        <div className="auth-divider">
          <span>или</span>
        </div>

        <div className="auth-oauth">
          <button className="auth-oauth-btn" onClick={handleGoogle}>
            <svg width="18" height="18" viewBox="0 0 18 18">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
              <path fill="#FBBC05" d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"/>
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z"/>
            </svg>
            Google
          </button>

          <button className="auth-oauth-btn" onClick={handleYandex}>
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path fill="#FC3F1D" d="M2.04 12c0-5.523 4.476-10 9.999-10C17.523 2 22 6.477 22 12s-4.477 10-10.001 10C6.516 22 2.04 17.523 2.04 12z"/>
              <path fill="#fff" d="M13.32 7.666h-.924c-1.694 0-2.585.858-2.585 2.123 0 1.43.616 2.1 1.881 2.959l1.045.704-3.003 4.548H7.49l2.695-4.086c-1.55-1.111-2.42-2.19-2.42-4.025 0-2.288 1.584-3.83 4.576-3.83h2.574v11.94H13.32V7.666z"/>
            </svg>
            Яндекс
          </button>
        </div>
      </div>
    </div>
  );
}

export default Auth;