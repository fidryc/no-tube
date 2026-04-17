import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import App from './App.jsx';
import GoogleCallback from './components/GoogleCallback/GoogleCallback.jsx';
import Auth from './components/Auth/Auth.jsx';
import YandexCallback from './components/YandexCallback/YandexCallback.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/callback" element={<GoogleCallback />} />
        <Route path="/callback_yandex" element={<YandexCallback />} />
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);