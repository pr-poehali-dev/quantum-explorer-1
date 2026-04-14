import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { auth, shop } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';

const STATUS_LABELS: Record<string, string> = {
  new: 'Новый', processing: 'В обработке', shipped: 'Отправлен', delivered: 'Доставлен', cancelled: 'Отменён'
};
const STATUS_COLORS: Record<string, string> = {
  new: 'default', processing: 'secondary', shipped: 'secondary', delivered: 'default', cancelled: 'destructive'
};

interface Order {
  id: number; status: string; total: number; name: string; phone: string;
  address: string; comment: string; created_at: string;
  items: Array<{ name: string; price: number; quantity: number }>;
}

export default function ProfilePage() {
  const { user, logout, refreshUser, loading } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!loading && !user) navigate('/login');
  }, [user, loading, navigate]);

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setPhone(user.phone || '');
      setAddress(user.address || '');
      shop.getOrders().then(d => setOrders(d.orders || [])).catch(() => {});
    }
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await auth.updateProfile({ name, phone, address });
      await refreshUser();
      toast.success('Профиль сохранён');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await auth.changePassword(oldPwd, newPwd);
      toast.success('Пароль изменён');
      setOldPwd(''); setNewPwd('');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    }
  };

  const handleLogout = () => { logout(); navigate('/'); };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to="/" className="text-primary text-sm font-mono hover:underline">← На главную</Link>
            <h1 className="text-2xl font-bold text-foreground font-mono mt-1">Профиль</h1>
          </div>
          <Button variant="outline" size="sm" onClick={handleLogout} className="font-mono">
            <Icon name="LogOut" size={15} className="mr-2" /> Выйти
          </Button>
        </div>

        <div className="bg-card border border-border rounded-2xl p-4 mb-6 flex items-center gap-3">
          <div className="bg-primary/10 rounded-full p-3">
            <Icon name="User" size={20} className="text-primary" />
          </div>
          <div>
            <p className="font-mono font-bold text-foreground">{user.name || user.email}</p>
            <p className="font-mono text-sm text-muted-foreground">{user.email}</p>
          </div>
          {user.role === 'admin' && <Badge className="ml-auto font-mono">admin</Badge>}
        </div>

        <Tabs defaultValue="orders">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="orders" className="flex-1">Мои заказы</TabsTrigger>
            <TabsTrigger value="profile" className="flex-1">Профиль</TabsTrigger>
            <TabsTrigger value="security" className="flex-1">Безопасность</TabsTrigger>
          </TabsList>

          <TabsContent value="orders">
            <div className="space-y-3">
              {orders.map(order => (
                <div key={order.id} className="bg-card border border-border rounded-2xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-bold text-foreground">Заказ #{order.id}</span>
                    <Badge variant={STATUS_COLORS[order.status] as 'default' | 'secondary' | 'destructive'} className="font-mono text-xs">
                      {STATUS_LABELS[order.status] || order.status}
                    </Badge>
                  </div>
                  <p className="text-xs font-mono text-muted-foreground mb-2">{new Date(order.created_at).toLocaleDateString('ru-RU')}</p>
                  <div className="space-y-0.5 mb-2">
                    {order.items.map((item, i) => (
                      <p key={i} className="text-xs font-mono text-muted-foreground">
                        {item.name} × {item.quantity} — {(item.price * item.quantity).toLocaleString()} ₽
                      </p>
                    ))}
                  </div>
                  <p className="font-mono font-bold text-primary">{order.total.toLocaleString()} ₽</p>
                </div>
              ))}
              {orders.length === 0 && (
                <div className="text-center py-10 text-muted-foreground font-mono">
                  <Icon name="ShoppingBag" size={32} className="mx-auto mb-3 opacity-30" />
                  <p>Заказов пока нет</p>
                  <Button asChild className="mt-4"><Link to="/">Перейти в каталог</Link></Button>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="profile">
            <form onSubmit={handleSaveProfile} className="bg-card border border-border rounded-2xl p-6 space-y-4">
              <div><Label>Имя</Label><Input value={name} onChange={e => setName(e.target.value)} className="mt-1" /></div>
              <div><Label>Телефон</Label><Input value={phone} onChange={e => setPhone(e.target.value)} className="mt-1" placeholder="+7 (999) 000-00-00" /></div>
              <div><Label>Адрес доставки</Label><Input value={address} onChange={e => setAddress(e.target.value)} className="mt-1" placeholder="Город, улица, дом" /></div>
              <Button type="submit" className="w-full" disabled={saving}>{saving ? 'Сохраняем...' : 'Сохранить'}</Button>
            </form>
          </TabsContent>

          <TabsContent value="security">
            <form onSubmit={handleChangePassword} className="bg-card border border-border rounded-2xl p-6 space-y-4">
              <div><Label>Текущий пароль</Label><Input type="password" value={oldPwd} onChange={e => setOldPwd(e.target.value)} className="mt-1" required /></div>
              <div><Label>Новый пароль</Label><Input type="password" value={newPwd} onChange={e => setNewPwd(e.target.value)} className="mt-1" placeholder="Минимум 6 символов" required /></div>
              <Button type="submit" className="w-full">Изменить пароль</Button>
            </form>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
