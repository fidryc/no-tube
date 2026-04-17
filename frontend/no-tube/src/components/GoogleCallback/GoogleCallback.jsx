import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './GoogleCallback.css';

function GoogleCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');

    if (!code) {
      setError('Код авторизации не найден');
      return;
    }

    fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/google/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) throw new Error('Ошибка авторизации');
        navigate('/');
      })
      .catch(err => {
        console.error(err);
        setError('Ошибка авторизации');
      });
  }, []);

  if (error) return (
    <div className="auth-container">
      <span className="auth-error">{error}</span>
    </div>
  );

  return (
    <div className="auth-container">
      <span className="auth-message">Авторизация...</span>
    </div>
  );
}

export default GoogleCallback;