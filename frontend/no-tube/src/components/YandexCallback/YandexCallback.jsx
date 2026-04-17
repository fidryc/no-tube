import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function YandexCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    // Яндекс возвращает токен в хэше: #access_token=xxx&token_type=bearer&...
    const hash = window.location.hash.substring(1); // убираем #
    const params = new URLSearchParams(hash);
    const access_token = params.get('access_token');

    if (!access_token) {
      setError('Токен авторизации не найден');
      return;
    }

    fetch(`${import.meta.env.VITE_API_URL}/api/v1/user/yandex/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ access_token }),
    })
      .then(res => {
        if (!res.ok) throw new Error('Ошибка авторизации');
        navigate('/');
      })
      .catch(err => {
        console.error(err);
        setError('Ошибка авторизации через Яндекс');
      });
  }, []);

  if (error) return (
    <div className="auth-container">
      <span className="auth-error">{error}</span>
    </div>
  );

  return (
    <div className="auth-container">
      <span className="auth-message">Авторизация через Яндекс...</span>
    </div>
  );
}

export default YandexCallback;