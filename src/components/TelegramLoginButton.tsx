import { useEffect, useRef } from 'react';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface Props {
  onAuth: (user: TelegramUser) => void;
}

const BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || '';

export default function TelegramLoginButton({ onAuth }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!BOT_USERNAME || !ref.current) return;

    (window as Record<string, unknown>)['onTelegramAuth'] = (user: TelegramUser) => {
      onAuth(user);
    };

    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', BOT_USERNAME);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    ref.current.innerHTML = '';
    ref.current.appendChild(script);

    return () => {
      delete (window as Record<string, unknown>)['onTelegramAuth'];
    };
  }, [onAuth]);

  if (!BOT_USERNAME) return null;

  return <div ref={ref} className="flex justify-center" />;
}
