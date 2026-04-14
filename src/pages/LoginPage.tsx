import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { auth } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';
import YandexOAuthButton from '@/components/YandexOAuthButton';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [notVerified, setNotVerified] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setNotVerified(false);
    try {
      await login(email, password);
      toast.success('Добро пожаловать!');
      navigate('/profile');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка';
      if (msg === 'EMAIL_NOT_VERIFIED') {
        setNotVerified(true);
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await auth.resendVerification(email);
      toast.success('Письмо отправлено повторно');
    } catch {
      toast.error('Не удалось отправить письмо');
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold text-foreground" style={{ fontFamily: 'var(--font-montserrat)' }}>
            🍬 SweetShop
          </Link>
          <h1 className="text-xl font-bold text-foreground font-mono mt-4">Войти</h1>
          <p className="text-muted-foreground font-mono text-sm mt-1">Введите email и пароль</p>
        </div>

        <div className="bg-card border border-border rounded-2xl p-6">
          {notVerified && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-4">
              <p className="text-sm font-mono text-yellow-600 dark:text-yellow-400 mb-2">
                📬 Email не подтверждён. Проверьте почту или запросите новое письмо.
              </p>
              <Button variant="outline" size="sm" className="w-full" onClick={handleResend}>
                Отправить письмо повторно
              </Button>
            </div>
          )}
          <YandexOAuthButton label="Войти через Яндекс" />
          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs text-muted-foreground font-mono">или</span>
            <div className="flex-1 h-px bg-border" />
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Email</Label>
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} className="mt-1" placeholder="you@example.com" required />
            </div>
            <div>
              <Label>Пароль</Label>
              <Input type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1" placeholder="Ваш пароль" required />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Входим...' : 'Войти'}
              {!loading && <Icon name="ArrowRight" size={16} className="ml-2" />}
            </Button>
          </form>
          <p className="text-center text-sm font-mono text-muted-foreground mt-4">
            Нет аккаунта?{' '}
            <Link to="/register" className="text-primary hover:underline">Зарегистрироваться</Link>
          </p>
        </div>
        <p className="text-center mt-4">
          <Link to="/" className="text-muted-foreground text-sm font-mono hover:underline">← На главную</Link>
        </p>
      </div>
    </div>
  );
}