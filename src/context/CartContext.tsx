import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { shop } from '@/lib/api';

interface CartItem {
  cart_id: number;
  product_id: number;
  name: string;
  price: number;
  quantity: number;
  emoji?: string;
  image_url?: string;
}

interface CartContextType {
  items: CartItem[];
  totalCount: number;
  totalPrice: number;
  addToCart: (product_id: number) => Promise<void>;
  updateQuantity: (product_id: number, quantity: number) => Promise<void>;
  refreshCart: () => Promise<void>;
  clearLocalCart: () => void;
}

const CartContext = createContext<CartContextType | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);

  const refreshCart = useCallback(async () => {
    try {
      const data = await shop.getCart();
      setItems(data.items || []);
    } catch {
      setItems([]);
    }
  }, []);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const addToCart = async (product_id: number) => {
    await shop.addToCart(product_id);
    await refreshCart();
  };

  const updateQuantity = async (product_id: number, quantity: number) => {
    await shop.updateCart(product_id, quantity);
    await refreshCart();
  };

  const clearLocalCart = () => setItems([]);

  const totalCount = items.reduce((sum, i) => sum + i.quantity, 0);
  const totalPrice = items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  return (
    <CartContext.Provider value={{ items, totalCount, totalPrice, addToCart, updateQuantity, refreshCart, clearLocalCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within CartProvider');
  return ctx;
}