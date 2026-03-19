import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { admin } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';

const ORDER_STATUSES = ['new', 'processing', 'shipped', 'delivered', 'cancelled'];
const STATUS_LABELS: Record<string, string> = { new: 'Новый', processing: 'В обработке', shipped: 'Отправлен', delivered: 'Доставлен', cancelled: 'Отменён' };

interface Product { id: number; name: string; description: string; price: number; emoji: string; image_url: string; in_stock: boolean; }
interface Order { id: number; status: string; total: number; name: string; phone: string; address: string; comment: string; created_at: string; user_email: string; items: Array<{name: string; price: number; quantity: number}>; }
interface User { id: number; email: string; name: string; phone: string; role: string; created_at: string; }
interface Stats { orders_count: number; revenue: number; users_count: number; products_count: number; new_orders: number; }

export default function AdminPage() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [editProduct, setEditProduct] = useState<Partial<Product> | null>(null);
  const [productDialogOpen, setProductDialogOpen] = useState(false);

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) { navigate('/login'); }
  }, [user, loading, navigate]);

  useEffect(() => {
    if (user?.role === 'admin') {
      admin.getStats().then(d => setStats(d)).catch(() => {});
      admin.getProducts().then(d => setProducts(d.products || [])).catch(() => {});
      admin.getOrders().then(d => setOrders(d.orders || [])).catch(() => {});
      admin.getUsers().then(d => setUsers(d.users || [])).catch(() => {});
    }
  }, [user]);

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editProduct) return;
    try {
      if (editProduct.id) {
        await admin.updateProduct(editProduct);
        toast.success('Товар обновлён');
      } else {
        await admin.createProduct(editProduct);
        toast.success('Товар добавлен');
      }
      setProductDialogOpen(false);
      const d = await admin.getProducts();
      setProducts(d.products || []);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка');
    }
  };

  const handleDeleteProduct = async (id: number) => {
    await admin.deleteProduct(id);
    toast.success('Товар снят с продажи');
    const d = await admin.getProducts();
    setProducts(d.products || []);
  };

  const handleUpdateOrderStatus = async (id: number, status: string) => {
    await admin.updateOrder(id, status);
    const d = await admin.getOrders();
    setOrders(d.orders || []);
    toast.success('Статус обновлён');
  };

  const handleUpdateUserRole = async (id: number, role: string) => {
    await admin.updateUser(id, role);
    const d = await admin.getUsers();
    setUsers(d.users || []);
    toast.success('Роль обновлена');
  };

  if (loading || !user) return null;

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to="/" className="text-primary text-sm font-mono hover:underline">← На сайт</Link>
            <h1 className="text-2xl font-bold text-foreground font-mono mt-1">Панель администратора</h1>
          </div>
          <Badge variant="secondary" className="font-mono">admin</Badge>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            {[
              { label: 'Заказов', value: stats.orders_count, icon: 'ShoppingBag' },
              { label: 'Новых', value: stats.new_orders, icon: 'Bell' },
              { label: 'Выручка', value: `${stats.revenue.toLocaleString()} ₽`, icon: 'TrendingUp' },
              { label: 'Клиентов', value: stats.users_count, icon: 'Users' },
              { label: 'Товаров', value: stats.products_count, icon: 'Package' },
            ].map(s => (
              <div key={s.label} className="bg-card border border-border rounded-xl p-4 text-center">
                <Icon name={s.icon as Parameters<typeof Icon>[0]['name']} size={20} className="mx-auto mb-1 text-primary" />
                <p className="text-xl font-bold text-foreground font-mono">{s.value}</p>
                <p className="text-xs text-muted-foreground font-mono">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        <Tabs defaultValue="orders">
          <TabsList className="w-full mb-6">
            <TabsTrigger value="orders" className="flex-1">Заказы</TabsTrigger>
            <TabsTrigger value="products" className="flex-1">Товары</TabsTrigger>
            <TabsTrigger value="users" className="flex-1">Пользователи</TabsTrigger>
          </TabsList>

          <TabsContent value="orders">
            <div className="space-y-3">
              {orders.map(order => (
                <div key={order.id} className="bg-card border border-border rounded-xl p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                    <div>
                      <span className="font-mono font-bold text-foreground">Заказ #{order.id}</span>
                      <span className="text-xs text-muted-foreground font-mono ml-3">{order.user_email}</span>
                      <span className="text-xs text-muted-foreground font-mono ml-3">{new Date(order.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                    <Select value={order.status} onValueChange={v => handleUpdateOrderStatus(order.id, v)}>
                      <SelectTrigger className="w-36 h-8 text-xs font-mono"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {ORDER_STATUSES.map(s => <SelectItem key={s} value={s} className="font-mono text-xs">{STATUS_LABELS[s]}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="text-sm font-mono text-muted-foreground mb-1">{order.name} · {order.phone}</div>
                  <div className="text-sm font-mono text-muted-foreground mb-2">{order.address}</div>
                  <div className="space-y-0.5 mb-2">
                    {order.items.map((item, i) => (
                      <div key={i} className="text-xs font-mono text-muted-foreground">{item.name} × {item.quantity} — {(item.price * item.quantity).toLocaleString()} ₽</div>
                    ))}
                  </div>
                  <div className="font-mono font-bold text-primary">{order.total.toLocaleString()} ₽</div>
                </div>
              ))}
              {orders.length === 0 && <p className="text-center text-muted-foreground font-mono py-8">Заказов пока нет</p>}
            </div>
          </TabsContent>

          <TabsContent value="products">
            <div className="flex justify-end mb-4">
              <Dialog open={productDialogOpen} onOpenChange={setProductDialogOpen}>
                <DialogTrigger asChild>
                  <Button onClick={() => setEditProduct({})}>
                    <Icon name="Plus" size={16} className="mr-2" /> Добавить товар
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle className="font-mono">{editProduct?.id ? 'Редактировать товар' : 'Новый товар'}</DialogTitle></DialogHeader>
                  <form onSubmit={handleSaveProduct} className="space-y-3">
                    <div><Label>Название</Label><Input value={editProduct?.name || ''} onChange={e => setEditProduct(p => ({...p, name: e.target.value}))} className="mt-1" required /></div>
                    <div><Label>Описание</Label><Input value={editProduct?.description || ''} onChange={e => setEditProduct(p => ({...p, description: e.target.value}))} className="mt-1" /></div>
                    <div><Label>Цена (₽)</Label><Input type="number" value={editProduct?.price || ''} onChange={e => setEditProduct(p => ({...p, price: Number(e.target.value)}))} className="mt-1" required /></div>
                    <div><Label>Эмодзи</Label><Input value={editProduct?.emoji || ''} onChange={e => setEditProduct(p => ({...p, emoji: e.target.value}))} className="mt-1" placeholder="🍫" /></div>
                    <div><Label>URL изображения</Label><Input value={editProduct?.image_url || ''} onChange={e => setEditProduct(p => ({...p, image_url: e.target.value}))} className="mt-1" /></div>
                    <Button type="submit" className="w-full">Сохранить</Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
            <div className="space-y-2">
              {products.map(product => (
                <div key={product.id} className="bg-card border border-border rounded-xl p-4 flex items-center gap-4">
                  <span className="text-2xl">{product.emoji || '📦'}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-mono font-bold text-foreground">{product.name}</p>
                    <p className="font-mono text-sm text-muted-foreground">{product.description}</p>
                  </div>
                  <span className="font-mono font-bold text-primary flex-shrink-0">{product.price.toLocaleString()} ₽</span>
                  <Badge variant={product.in_stock ? 'default' : 'destructive'} className="font-mono text-xs flex-shrink-0">
                    {product.in_stock ? 'В наличии' : 'Нет'}
                  </Badge>
                  <div className="flex gap-2 flex-shrink-0">
                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => { setEditProduct(product); setProductDialogOpen(true); }}>
                      <Icon name="Pencil" size={14} />
                    </Button>
                    <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => handleDeleteProduct(product.id)}>
                      <Icon name="EyeOff" size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="users">
            <div className="space-y-2">
              {users.map(u => (
                <div key={u.id} className="bg-card border border-border rounded-xl p-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-mono font-bold text-foreground">{u.name || '—'}</p>
                    <p className="font-mono text-sm text-muted-foreground">{u.email}</p>
                    {u.phone && <p className="font-mono text-xs text-muted-foreground">{u.phone}</p>}
                  </div>
                  <span className="font-mono text-xs text-muted-foreground flex-shrink-0">{new Date(u.created_at).toLocaleDateString('ru-RU')}</span>
                  <Select value={u.role} onValueChange={v => handleUpdateUserRole(u.id, v)}>
                    <SelectTrigger className="w-28 h-8 text-xs font-mono flex-shrink-0"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="user" className="font-mono text-xs">Клиент</SelectItem>
                      <SelectItem value="admin" className="font-mono text-xs">Админ</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
