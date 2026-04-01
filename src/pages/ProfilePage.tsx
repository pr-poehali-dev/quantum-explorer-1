import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { auth, shop } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';

const STATUS_MAP: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  new: { label: 'Новый', variant: 'default' },
  processing: { label: 'В обработке', variant: 'secondary' },
  shipped: { label: 'Отправлен', variant: 'secondary' },
  delivered: { label: 'Доставлен', variant: 'outline' },
  cancelled: { label: 'Отменён', variant: 'destructive' },
};

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [address, setAddress] = useState(user?.address || '');
  const [email, setEmail] = useState(user?.email || '');
  const [emailPassword, setEmailPassword] = useState('');
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [orders, setOrders] = useState<unknown[]>([]);
  const [saving, setSaving] = useState(false);
  const [changingPwd, setChangingPwd] = useState(false);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    setName(user.name || '');
    setPhone(user.phone || '');
    setAddress(user.address || '');
    setEmail(user.email || '');
    shop.getOrders().then(d => setOrders(d.orders || [])).catch(() => {});
  }, [user, navigate]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const emailChanged = email.trim().toLowerCase() !== (user?.email || '').toLowerCase();
      const payload: { name?: string; phone?: string; address?: string; email?: string; password?: string } = { name, phone, address };
      if (emailChanged) {
        if (!emailPassword) { toast.error('Введите пароль для смены email'); setSaving(false); return; }
        payload.email = email.trim().toLowerCase();
        payload.password = emailPassword;
      }
      await auth.updateProfile(payload);
      await refreshUser();
      setEmailPassword('');
      toast.success('Данные сохранены');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setChangingPwd(true);
    try {
      await auth.changePassword(oldPwd, newPwd);
      toast.success('Пароль изменён');
      setOldPwd(''); setNewPwd('');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setChangingPwd(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to="/" className="text-primary text-sm font-mono hover:underline">← На главную</Link>
            <h1 className="text-2xl font-bold text-foreground font-mono mt-1">Личный кабинет</h1>
            <p className="text-muted-foreground text-sm font-mono">{user.email}</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => { logout(); navigate('/'); }}>
            <Icon name="LogOut" size={16} className="mr-2" /> Выйти
          </Button>
        </div>

        <Tabs defaultValue="profile">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="profile" className="flex-1">Профиль</TabsTrigger>
            <TabsTrigger value="orders" className="flex-1">Мои заказы ({orders.length})</TabsTrigger>
            <TabsTrigger value="security" className="flex-1">Безопасность</TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <div className="bg-card border border-border rounded-2xl p-6">
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div>
                  <Label>Имя</Label>
                  <Input value={name} onChange={e => setName(e.target.value)} className="mt-1" placeholder="Ваше имя" />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input type="email" value={email} onChange={e => setEmail(e.target.value)} className="mt-1" placeholder="you@example.com" required />
                </div>
                {email.trim().toLowerCase() !== (user?.email || '').toLowerCase() && (
                  <div>
                    <Label>Пароль для подтверждения смены email</Label>
                    <Input type="password" value={emailPassword} onChange={e => setEmailPassword(e.target.value)} className="mt-1" placeholder="Введите текущий пароль" required />
                  </div>
                )}
                <div>
                  <Label>Телефон</Label>
                  <Input value={phone} onChange={e => setPhone(e.target.value)} className="mt-1" placeholder="+7 (999) 000-00-00" />
                </div>
                <div>
                  <Label>Адрес доставки</Label>
                  <Input value={address} onChange={e => setAddress(e.target.value)} className="mt-1" placeholder="Город, улица, дом, квартира" />
                </div>
                <Button type="submit" disabled={saving}>{saving ? 'Сохраняем...' : 'Сохранить изменения'}</Button>
              </form>
            </div>
          </TabsContent>

          <TabsContent value="orders">
            <div className="space-y-4">
              {orders.length === 0 && (
                <div className="bg-card border border-border rounded-2xl p-8 text-center">
                  <span className="text-4xl mb-3 block">🛍️</span>
                  <p className="text-muted-foreground font-mono">У вас пока нет заказов</p>
                  <Link to="/" className="mt-3 inline-block text-primary text-sm font-mono hover:underline">Перейти в каталог →</Link>
                </div>
              )}
              {(orders as Array<{id: number; status: string; total: number; created_at: string; address: string; items: Array<{name: string; quantity: number; price: number}>}>).map(order => {
                const statusInfo = STATUS_MAP[order.status] || { label: order.status, variant: 'default' as const };
                return (
                  <div key={order.id} className="bg-card border border-border rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono font-bold text-foreground">Заказ #{order.id}</span>
                      <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                    </div>
                    <div className="space-y-1 mb-3">
                      {order.items.map((item, i) => (
                        <div key={i} className="flex justify-between text-sm font-mono text-muted-foreground">
                          <span>{item.name} × {item.quantity}</span>
                          <span>{(item.price * item.quantity).toLocaleString()} ₽</span>
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-between items-center border-t border-border pt-3">
                      <span className="text-xs text-muted-foreground font-mono">{new Date(order.created_at).toLocaleDateString('ru-RU')}</span>
                      <span className="font-mono font-bold text-primary">{order.total.toLocaleString()} ₽</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value="security">
            <div className="bg-card border border-border rounded-2xl p-6">
              <h2 className="font-mono font-bold text-foreground mb-4">Изменить пароль</h2>
              <form onSubmit={handleChangePassword} className="space-y-4">
                <div>
                  <Label>Текущий пароль</Label>
                  <Input type="password" value={oldPwd} onChange={e => setOldPwd(e.target.value)} className="mt-1" required />
                </div>
                <div>
                  <Label>Новый пароль</Label>
                  <Input type="password" value={newPwd} onChange={e => setNewPwd(e.target.value)} className="mt-1" placeholder="Минимум 6 символов" required />
                </div>
                <Button type="submit" disabled={changingPwd}>{changingPwd ? 'Меняем...' : 'Изменить пароль'}</Button>
              </form>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}