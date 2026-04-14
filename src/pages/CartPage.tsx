import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '@/context/CartContext';
import { shop } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import Icon from '@/components/ui/icon';

export default function CartPage() {
  const { items, totalPrice, updateQuantity, refreshCart } = useCart();
  const navigate = useNavigate();
  const [step, setStep] = useState<'cart' | 'checkout'>('cart');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [comment, setComment] = useState('');
  const [placing, setPlacing] = useState(false);

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (items.length === 0) { toast.error('Корзина пуста'); return; }
    setPlacing(true);
    try {
      const data = await shop.createOrder({ name, phone, address, comment });
      await refreshCart();
      toast.success(`Заказ #${data.order_id} оформлен!`);
      navigate('/');
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Ошибка оформления');
    } finally {
      setPlacing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Link to="/" className="text-primary text-sm font-mono hover:underline">← На главную</Link>
        </div>

        {step === 'cart' && (
          <>
            <h1 className="text-2xl font-bold text-foreground font-mono mb-6">Корзина</h1>
            {items.length === 0 ? (
              <div className="bg-card border border-border rounded-2xl p-8 text-center">
                <span className="text-4xl mb-3 block">🛒</span>
                <p className="text-muted-foreground font-mono mb-4">Корзина пуста</p>
                <Button asChild><Link to="/">Перейти в каталог</Link></Button>
              </div>
            ) : (
              <>
                <div className="space-y-3 mb-6">
                  {items.map(item => (
                    <div key={item.product_id} className="bg-card border border-border rounded-2xl p-4 flex items-center gap-4">
                      <div className="text-3xl flex-shrink-0">
                        {item.image_url ? <img src={item.image_url} className="w-12 h-12 rounded-xl object-cover" alt={item.name} /> : item.emoji}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-mono font-bold text-foreground truncate">{item.name}</p>
                        <p className="font-mono text-primary text-sm">{item.price.toLocaleString()} ₽ / шт.</p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Button variant="outline" size="icon" className="h-8 w-8"
                          onClick={() => updateQuantity(item.product_id, item.quantity - 1)}>
                          <Icon name="Minus" size={14} />
                        </Button>
                        <span className="font-mono w-6 text-center text-foreground">{item.quantity}</span>
                        <Button variant="outline" size="icon" className="h-8 w-8"
                          onClick={() => updateQuantity(item.product_id, item.quantity + 1)}>
                          <Icon name="Plus" size={14} />
                        </Button>
                      </div>
                      <span className="font-mono font-bold text-foreground w-20 text-right flex-shrink-0">
                        {(item.price * item.quantity).toLocaleString()} ₽
                      </span>
                    </div>
                  ))}
                </div>
                <div className="bg-card border border-border rounded-2xl p-5 flex items-center justify-between">
                  <span className="font-mono text-foreground font-bold">Итого:</span>
                  <span className="font-mono text-primary font-bold text-xl">{totalPrice.toLocaleString()} ₽</span>
                </div>
                <Button className="w-full mt-4" size="lg" onClick={() => setStep('checkout')}>
                  Оформить заказ <Icon name="ArrowRight" size={16} className="ml-2" />
                </Button>
              </>
            )}
          </>
        )}

        {step === 'checkout' && (
          <>
            <div className="flex items-center gap-3 mb-6">
              <button onClick={() => setStep('cart')} className="text-primary text-sm font-mono hover:underline">← Назад в корзину</button>
            </div>
            <h1 className="text-2xl font-bold text-foreground font-mono mb-6">Оформление заказа</h1>
            <div className="bg-card border border-border rounded-2xl p-5 mb-4">
              <p className="font-mono text-sm text-muted-foreground mb-2">Товаров: {items.reduce((s, i) => s + i.quantity, 0)} шт.</p>
              <p className="font-mono font-bold text-primary text-lg">Итого: {totalPrice.toLocaleString()} ₽</p>
            </div>
            <form onSubmit={handlePlaceOrder} className="bg-card border border-border rounded-2xl p-6 space-y-4">
              <div>
                <Label>Имя получателя</Label>
                <Input value={name} onChange={e => setName(e.target.value)} className="mt-1" required />
              </div>
              <div>
                <Label>Телефон</Label>
                <Input value={phone} onChange={e => setPhone(e.target.value)} className="mt-1" placeholder="+7 (999) 000-00-00" required />
              </div>
              <div>
                <Label>Адрес доставки</Label>
                <Input value={address} onChange={e => setAddress(e.target.value)} className="mt-1" placeholder="Город, улица, дом, квартира" required />
              </div>
              <div>
                <Label>Комментарий к заказу</Label>
                <Textarea value={comment} onChange={e => setComment(e.target.value)} className="mt-1" placeholder="Пожелания, удобное время доставки..." rows={3} />
              </div>
              <Button type="submit" className="w-full" size="lg" disabled={placing}>
                {placing ? 'Оформляем...' : 'Подтвердить заказ'}
              </Button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}