const YANDEX_CLIENT_ID = import.meta.env.VITE_YANDEX_CLIENT_ID || '';

export function startYandexOAuth() {
  const redirectUri = `${window.location.origin}/oauth/yandex/callback`;
  const state = crypto.randomUUID();
  sessionStorage.setItem('yandex_oauth_state', state);

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: YANDEX_CLIENT_ID,
    redirect_uri: redirectUri,
    state,
    force_confirm: 'no',
  });

  window.location.href = `https://oauth.yandex.ru/authorize?${params.toString()}`;
}
