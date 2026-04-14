import { useEffect, useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { auth } from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login: _login } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) { setStatus('error'); setErrorMsg('Токен не найден'); return; }
    auth.verifyEmail(token)
      .then((data) => {
        localStorage.setItem('auth_token', data.token);
        setStatus('success');
        setTimeout(() => navigate('/profile'), 2000);
      })
      .catch((err: unknown) => {
        setStatus('error');
        setErrorMsg(err instanceof Error ? err.message : 'Ошибка подтверждения');
      });
  }, []);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="bg-card border border-border rounded-2xl p-8">
          {status === 'loading' && (
            <>
              <span className="text-5xl mb-4 block">⏳</span>
              <h2 className="text-xl font-bold text-foreground font-mono">Подтверждаем email...</h2>
            </>
          )}
          {status === 'success' && (
            <>
              <span className="text-5xl mb-4 block">✅</span>
              <h2 className="text-xl font-bold text-foreground font-mono mb-2">Email подтверждён!</h2>
              <p className="text-muted-foreground font-mono text-sm">Переходим в профиль...</p>
            </>
          )}
          {status === 'error' && (
            <>
              <span className="text-5xl mb-4 block">❌</span>
              <h2 className="text-xl font-bold text-foreground font-mono mb-2">Ошибка</h2>
              <p className="text-muted-foreground font-mono text-sm mb-6">{errorMsg}</p>
              <Button asChild className="w-full mb-3">
                <Link to="/register">Зарегистрироваться заново</Link>
              </Button>
              <Link to="/login" className="text-primary text-sm font-mono hover:underline">Войти</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
