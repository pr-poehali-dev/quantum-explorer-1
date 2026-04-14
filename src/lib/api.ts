const AUTH_URL = 'https://functions.poehali.dev/1349fb1d-e908-4bea-a29d-05db1322232d';
const SHOP_URL = 'https://functions.poehali.dev/59b0af84-8647-4b94-bafa-296c1e76d239';
const ADMIN_URL = 'https://functions.poehali.dev/ff10ae38-5a9d-4667-b65b-b5f20b9633c1';

function getToken() {
  return localStorage.getItem('auth_token') || '';
}

function getSessionId(): string {
  let sid = localStorage.getItem('session_id');
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem('session_id', sid);
  }
  return sid;
}

async function request(baseUrl: string, action: string, method = 'GET', body?: object, withSession = false) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (withSession) headers['X-Session-Id'] = getSessionId();
  const t = getToken();
  if (t) headers['X-Auth-Token'] = t;
  const res = await fetch(`${baseUrl}?action=${action}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Ошибка запроса');
  return data;
}

export const auth = {
  register: (email: string, password: string, name: string) =>
    request(AUTH_URL, 'register', 'POST', { email, password, name }),
  verifyEmail: (token: string) =>
    request(AUTH_URL, 'verify-email', 'POST', { token }),
  resendVerification: (email: string) =>
    request(AUTH_URL, 'resend-verification', 'POST', { email }),
  login: (email: string, password: string) =>
    request(AUTH_URL, 'login', 'POST', { email, password }),
  me: () => request(AUTH_URL, 'me'),
  updateProfile: (data: { name?: string; phone?: string; address?: string }) =>
    request(AUTH_URL, 'profile', 'PUT', data),
  changePassword: (old_password: string, new_password: string) =>
    request(AUTH_URL, 'password', 'PUT', { old_password, new_password }),
};

export const shop = {
  getProducts: () => request(SHOP_URL, 'products'),
  getCart: () => request(SHOP_URL, 'cart', 'GET', undefined, true),
  addToCart: (product_id: number, quantity = 1) =>
    request(SHOP_URL, 'cart', 'POST', { product_id, quantity }, true),
  updateCart: (product_id: number, quantity: number) =>
    request(SHOP_URL, 'cart', 'PUT', { product_id, quantity }, true),
  createOrder: (data: { name: string; phone: string; address: string; comment?: string }) =>
    request(SHOP_URL, 'orders', 'POST', data, true),
  getOrders: () => request(SHOP_URL, 'orders', 'GET', undefined, true),
};

export const admin = {
  getStats: () => request(ADMIN_URL, 'stats'),
  getProducts: () => request(ADMIN_URL, 'products'),
  createProduct: (data: object) => request(ADMIN_URL, 'products', 'POST', data),
  updateProduct: (data: object) => request(ADMIN_URL, 'products', 'PUT', data),
  deleteProduct: (id: number) => request(ADMIN_URL, 'products', 'DELETE', { id }),
  getOrders: () => request(ADMIN_URL, 'orders'),
  updateOrder: (id: number, status: string) => request(ADMIN_URL, 'orders', 'PUT', { id, status }),
  getUsers: () => request(ADMIN_URL, 'users'),
  updateUser: (id: number, role: string) => request(ADMIN_URL, 'users', 'PUT', { id, role }),
  getManagers: () => request(ADMIN_URL, 'managers'),
  createManager: (data: { email: string; name?: string }) => request(ADMIN_URL, 'managers', 'POST', data),
  updateManager: (data: { id: number; email: string; name?: string }) => request(ADMIN_URL, 'managers', 'PUT', data),
  deleteManager: (id: number) => request(ADMIN_URL, 'managers', 'DELETE', { id }),
};