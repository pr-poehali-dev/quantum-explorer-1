const SHOP_URL = 'https://functions.poehali.dev/59b0af84-8647-4b94-bafa-296c1e76d239';
const ADMIN_URL = 'https://functions.poehali.dev/ff10ae38-5a9d-4667-b65b-b5f20b9633c1';

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
  const res = await fetch(`${baseUrl}?action=${action}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Ошибка запроса');
  return data;
}

export const shop = {
  getProducts: () => request(SHOP_URL, 'products'),
  getCart: () => request(SHOP_URL, 'cart', 'GET', undefined, true),
  addToCart: (product_id: number, quantity = 1) =>
    request(SHOP_URL, 'cart', 'POST', { product_id, quantity }, true),
  updateCart: (product_id: number, quantity: number) =>
    request(SHOP_URL, 'cart', 'PUT', { product_id, quantity }, true),
  createOrder: (data: { name: string; phone: string; address: string; comment?: string; email?: string }) =>
    request(SHOP_URL, 'orders', 'POST', data, true),
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