import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { auth } from '@/lib/api';

export default function YandexCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const savedState = sessionStorage.getItem('yandex_oauth_state');

    if (!code) {
      setError('Код авторизации не получен от Яндекса');
      return;
    }
    if (state && savedState && state !== savedState) {
      setError('Ошибка безопасности: state не совпадает');
      return;
    }
    sessionStorage.removeItem('yandex_oauth_state');

    auth.yandexOAuth(code)
      .then((data) => {
        localStorage.setItem('auth_token', data.token);
        setUser(data.user);
        navigate('/profile', { replace: true });
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Ошибка входа через Яндекс');
      });
  }, []);

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center bg-card border border-border rounded-2xl p-8">
          <span className="text-5xl mb-4 block">❌</span>
          <h2 className="text-xl font-bold text-foreground font-mono mb-2">Ошибка входа</h2>
          <p className="text-muted-foreground font-mono text-sm mb-6">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="text-primary font-mono text-sm hover:underline"
          >
            ← Вернуться на страницу входа
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center bg-card border border-border rounded-2xl p-8">
        <span className="text-5xl mb-4 block animate-pulse">🟡</span>
        <h2 className="text-xl font-bold text-foreground font-mono">Входим через Яндекс...</h2>
      </div>
    </div>
  );
}
