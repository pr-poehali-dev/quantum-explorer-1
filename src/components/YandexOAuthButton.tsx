import { Button } from '@/components/ui/button';
import { startYandexOAuth } from '@/lib/yandex-oauth';

export default function YandexOAuthButton({ label = 'Войти через Яндекс' }: { label?: string }) {
  return (
    <Button
      type="button"
      variant="outline"
      className="w-full flex items-center gap-3 font-mono"
      onClick={startYandexOAuth}
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0z" fill="#FC3F1D"/>
        <path d="M13.32 7.219h-.924c-1.508 0-2.303.743-2.303 1.95 0 1.361.573 2.028 1.733 2.826l.963.651-2.759 4.135H8.134l2.523-3.787c-1.459-1.04-2.275-2.08-2.275-3.74 0-2.143 1.484-3.573 3.91-3.573h2.963v10.1H13.32V7.22z" fill="#fff"/>
      </svg>
      {label}
    </Button>
  );
}
