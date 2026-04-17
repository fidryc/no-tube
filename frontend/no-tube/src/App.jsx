import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/me`, {
      method: 'GET',
      credentials: 'include',
    })
      .then(res => {
        if (res.status === 401) return null;
        if (!res.ok) throw new Error('Ошибка сервера');
        return res.json();
      })
      .then(data => setUser(data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = async () => {
    try {
      await fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/quit`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error(err);
    }
    setUser(null);
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="app-loading-bar" />
      </div>
    );
  }

  return (
    <div className="app-page">
      <div className="app-grid-bg" />

      <header className="app-header">
        <div className="app-logo">▲ notube</div>
        {user && (
          <button className="app-logout" onClick={handleLogout}>
            Выйти
          </button>
        )}
      </header>

      <main className="app-main">
        {user ? (
          <div className="app-profile">
            <div className="app-avatar">
              {user.username[0].toUpperCase()}
            </div>
            <div className="app-profile-info">
              <h1 className="app-welcome">
                Привет, <span className="app-username">{user.username}</span>
              </h1>
              <div className="app-meta">
                <div className="app-meta-item">
                  <span className="app-meta-label">Email</span>
                  <span className="app-meta-value">{user.email}</span>
                </div>
                <div className="app-meta-item">
                  <span className="app-meta-label">Роль</span>
                  <span className={`app-role app-role--${user.role?.toLowerCase()}`}>
                    {user.role}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="app-guest">
            <div className="app-guest-icon">◈</div>
            <h1 className="app-guest-title">Добро пожаловать</h1>
            <p className="app-guest-sub">Войдите чтобы продолжить</p>
            <div className="app-guest-actions">
              <button className="app-btn-primary" onClick={() => navigate('/auth')}>
                Войти
              </button>
              <button className="app-btn-google" onClick={() => {
                window.location.href = `${import.meta.env.VITE_API_URL}/api/v1/user/google/url`;
              }}>
                <svg width="16" height="16" viewBox="0 0 18 18">
                  <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
                  <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
                  <path fill="#FBBC05" d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"/>
                  <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z"/>
                </svg>
                Google
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;