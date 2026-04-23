import { useSearchParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

export default function OrderSuccessPage() {
  const [params] = useSearchParams();
  const orderId = params.get('order_id');

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="bg-card border border-border rounded-2xl p-10">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
              <Icon name="CheckCircle" size={36} className="text-green-600" />
            </div>
          </div>
          <h1 className="text-2xl font-bold font-mono text-foreground mb-2">Оплата прошла!</h1>
          {orderId && (
            <p className="text-muted-foreground font-mono text-sm mb-4">Заказ №{orderId}</p>
          )}
          <p className="text-muted-foreground font-mono text-sm mb-8">
            Спасибо за покупку. Мы получили ваш заказ и скоро свяжемся с вами.
          </p>
          <div className="flex flex-col gap-3">
            <Button asChild className="w-full">
              <Link to="/profile">Мои заказы</Link>
            </Button>
            <Button asChild variant="outline" className="w-full">
              <Link to="/">Продолжить покупки</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
