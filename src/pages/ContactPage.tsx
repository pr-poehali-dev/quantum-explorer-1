import { Link } from 'react-router-dom';
import Icon from '@/components/ui/icon';

const contacts = [
  {
    icon: 'MapPin',
    label: 'Адрес',
    value: 'г. Москва, ул. Кондитерская, д. 12',
    sub: 'Ближайшее метро: Сокольники',
    href: 'https://yandex.ru/maps/?text=Москва+Кондитерская+12',
  },
  {
    icon: 'Phone',
    label: 'Телефон',
    value: '+7 (495) 123-45-67',
    sub: 'Пн–Пт: 10:00 – 20:00',
    href: 'tel:+74951234567',
  },
  {
    icon: 'Mail',
    label: 'Email',
    value: 'hello@sweetshop.ru',
    sub: 'Отвечаем в течение часа',
    href: 'mailto:hello@sweetshop.ru',
  },
  {
    icon: 'Clock',
    label: 'Режим работы',
    value: 'Пн–Пт: 10:00 – 20:00',
    sub: 'Сб–Вс: 11:00 – 18:00',
    href: null,
  },
];

const socials = [
  { icon: 'MessageCircle', label: 'Telegram', href: 'https://t.me/sweetshop' },
  { icon: 'Instagram', label: 'Instagram', href: 'https://instagram.com/sweetshop' },
  { icon: 'Phone', label: 'WhatsApp', href: 'https://wa.me/74951234567' },
];

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-background px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Link to="/" className="text-primary text-sm font-mono hover:underline">
            ← На главную
          </Link>
          <h1 className="text-2xl font-bold text-foreground font-mono mt-2">Контакты</h1>
          <p className="text-muted-foreground text-sm font-mono mt-1">
            Всегда рады помочь с выбором и доставкой
          </p>
        </div>

        <div className="space-y-4 mb-8">
          {contacts.map((item) => (
            <div key={item.label} className="bg-card border border-border rounded-2xl p-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Icon name={item.icon as Parameters<typeof Icon>[0]['name']} size={20} className="text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-muted-foreground font-mono mb-1">{item.label}</p>
                  {item.href ? (
                    <a
                      href={item.href}
                      target={item.href.startsWith('http') ? '_blank' : undefined}
                      rel="noopener noreferrer"
                      className="font-mono font-semibold text-foreground hover:text-primary transition-colors"
                    >
                      {item.value}
                    </a>
                  ) : (
                    <p className="font-mono font-semibold text-foreground">{item.value}</p>
                  )}
                  <p className="text-xs text-muted-foreground font-mono mt-1">{item.sub}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-card border border-border rounded-2xl p-5 mb-8">
          <p className="text-xs text-muted-foreground font-mono mb-3">Мы в соцсетях</p>
          <div className="flex gap-3">
            {socials.map((s) => (
              <a
                key={s.label}
                href={s.href}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-background border border-border rounded-xl px-4 py-2 text-sm font-mono text-foreground hover:border-primary hover:text-primary transition-colors"
              >
                <Icon name={s.icon as Parameters<typeof Icon>[0]['name']} size={16} />
                {s.label}
              </a>
            ))}
          </div>
        </div>

        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-border">
            <p className="text-xs text-muted-foreground font-mono mb-0.5">Мы на карте</p>
            <p className="font-mono font-semibold text-foreground text-sm">г. Москва, ул. Кондитерская, д. 12</p>
          </div>
          <div className="h-64 bg-muted flex items-center justify-center">
            <a
              href="https://yandex.ru/maps/?text=Москва+Кондитерская+12"
              target="_blank"
              rel="noopener noreferrer"
              className="flex flex-col items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
            >
              <Icon name="MapPin" size={32} />
              <span className="font-mono text-sm">Открыть на Яндекс.Картах</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
