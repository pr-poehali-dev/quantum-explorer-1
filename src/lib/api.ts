const AUTH_URL = 'https://functions.poehali.dev/1349fb1d-e908-4bea-a29d-05db1322232d';
const SHOP_URL = 'https://functions.poehali.dev/59b0af84-8647-4b94-bafa-296c1e76d239';
const ADMIN_URL = 'https://functions.poehali.dev/ff10ae38-5a9d-4667-b65b-b5f20b9633c1';

function getToken() {
  return localStorage.getItem('auth_token') || '';
}

async function request(baseUrl: string, action: string, method = 'GET', body?: object) {
  const res = await fetch(`${baseUrl}?action=${action}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Auth-Token': getToken(),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Ошибка запроса');
  return data;
}

export const auth = {
  register: (email: string, password: string, name: string) =>
    request(AUTH_URL, 'register', 'POST', { email, password, name }),
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
  getCart: () => request(SHOP_URL, 'cart'),
  addToCart: (product_id: number, quantity = 1) =>
    request(SHOP_URL, 'cart', 'POST', { product_id, quantity }),
  updateCart: (product_id: number, quantity: number) =>
    request(SHOP_URL, 'cart', 'PUT', { product_id, quantity }),
  createOrder: (data: { name: string; phone: string; address: string; comment?: string }) =>
    request(SHOP_URL, 'orders', 'POST', data),
  getOrders: () => request(SHOP_URL, 'orders'),
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
};
