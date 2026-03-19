
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255),
  phone VARCHAR(50),
  address TEXT,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price INTEGER NOT NULL,
  emoji VARCHAR(10),
  image_url TEXT,
  button_class VARCHAR(255),
  in_stock BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cart_items (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  product_id INTEGER REFERENCES products(id),
  quantity INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, product_id)
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  status VARCHAR(50) NOT NULL DEFAULT 'new',
  total INTEGER NOT NULL DEFAULT 0,
  name VARCHAR(255),
  phone VARCHAR(50),
  address TEXT,
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id),
  product_id INTEGER REFERENCES products(id),
  product_name VARCHAR(255) NOT NULL,
  product_price INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 1
);

INSERT INTO users (email, password_hash, name, role) VALUES
('admin@shop.ru', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGniXoeFhYrGpAUc7nP.7BHFbOe', 'Администратор', 'admin');

INSERT INTO products (name, description, price, emoji, image_url, button_class) VALUES
('Бельгийский шоколад', 'Ручная работа, натуральное какао', 890, NULL, 'https://cdn.poehali.dev/projects/68b98fe6-18ec-42a9-8d59-af1b4f9af3ca/files/38a3d27d-cd8b-456a-a147-e2182e1ac86f.jpg', 'bg-[#9B59B6] hover:bg-[#A96BC8]'),
('Макаруны ассорти', '12 штук, 6 вкусов', 1290, '🧁', NULL, NULL),
('Подарочный набор', 'Конфеты, мармелад, пастила', 2490, '🎁', NULL, NULL),
('Медовая пастила', 'Яблочная, с облепихой и вишней', 590, '🍯', NULL, NULL),
('Трюфели ручной работы', '9 штук, тёмный и молочный шоколад', 1490, '🍬', NULL, NULL),
('Фруктовый мармелад', 'Без сахара, на натуральном соке', 690, '🍊', NULL, NULL);
