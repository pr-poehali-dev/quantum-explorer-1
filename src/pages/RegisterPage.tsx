import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) { toast.error('Пароль минимум 6 символов'); return; }
    setLoading(true);
    try {
      await register(email, password, name);
      toast.success('Аккаунт создан!');
      navigate('/profile');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка регистрации');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl p-8">
        <h1 className="text-2xl font-bold text-foreground mb-2 font-mono">Регистрация</h1>
        <p className="text-muted-foreground text-sm mb-6 font-mono">Создайте аккаунт для заказов</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Имя</Label>
            <Input id="name" type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Ваше имя" className="mt-1" />
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required className="mt-1" />
          </div>
          <div>
            <Label htmlFor="password">Пароль</Label>
            <Input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Минимум 6 символов" required className="mt-1" />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Создаём...' : 'Создать аккаунт'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-muted-foreground font-mono">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-primary hover:underline">Войти</Link>
        </p>
        <p className="mt-2 text-center text-sm text-muted-foreground font-mono">
          <Link to="/" className="text-primary hover:underline">← На главную</Link>
        </p>
      </div>
    </div>
  );
}
