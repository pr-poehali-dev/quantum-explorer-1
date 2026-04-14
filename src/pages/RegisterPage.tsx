import { useState } from 'react';
import { Link } from 'react-router-dom';
import { auth } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [sentEmail, setSentEmail] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) { toast.error('Пароль минимум 6 символов'); return; }
    setLoading(true);
    try {
      await auth.register(email, password, name);
      setSentEmail(email);
      setDone(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ошибка';
      if (msg === 'EMAIL_NOT_VERIFIED') {
        setSentEmail(email);
        setDone(true);
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      await auth.resendVerification(sentEmail);
      toast.success('Письмо отправлено повторно');
    } catch {
      toast.error('Не удалось отправить письмо');
    }
  };

  if (done) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="w-full max-w-md text-center">
          <div className="bg-card border border-border rounded-2xl p-8">
            <span className="text-5xl mb-4 block">📬</span>
            <h2 className="text-xl font-bold text-foreground font-mono mb-2">Проверьте почту</h2>
            <p className="text-muted-foreground font-mono text-sm mb-1">
              Мы отправили письмо на
            </p>
            <p className="text-primary font-mono font-bold mb-4">{sentEmail}</p>
            <p className="text-muted-foreground font-mono text-sm mb-6">
              Перейдите по ссылке в письме, чтобы подтвердить email и войти в магазин.
            </p>
            <Button variant="outline" className="w-full mb-3" onClick={handleResend}>
              Отправить письмо повторно
            </Button>
            <Link to="/login" className="text-primary text-sm font-mono hover:underline">
              Уже подтвердили? Войти
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold text-foreground" style={{ fontFamily: 'var(--font-montserrat)' }}>
            🍬 SweetShop
          </Link>
          <h1 className="text-xl font-bold text-foreground font-mono mt-4">Регистрация</h1>
          <p className="text-muted-foreground font-mono text-sm mt-1">Создайте аккаунт для оформления заказов</p>
        </div>
        <div className="bg-card border border-border rounded-2xl p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Имя</Label>
              <Input value={name} onChange={e => setName(e.target.value)} className="mt-1" placeholder="Иван Иванов" />
            </div>
            <div>
              <Label>Email <span className="text-destructive">*</span></Label>
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} className="mt-1" placeholder="you@example.com" required />
            </div>
            <div>
              <Label>Пароль <span className="text-destructive">*</span></Label>
              <Input type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1" placeholder="Минимум 6 символов" required />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Регистрируем...' : 'Зарегистрироваться'}
              {!loading && <Icon name="ArrowRight" size={16} className="ml-2" />}
            </Button>
          </form>
          <p className="text-center text-sm font-mono text-muted-foreground mt-4">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-primary hover:underline">Войти</Link>
          </p>
        </div>
        <p className="text-center mt-4">
          <Link to="/" className="text-muted-foreground text-sm font-mono hover:underline">← На главную</Link>
        </p>
      </div>
    </div>
  );
}
