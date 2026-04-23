ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS order_number VARCHAR(50);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS user_name VARCHAR(255);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS user_phone VARCHAR(50);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS yookassa_payment_id VARCHAR(100);
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS payment_url TEXT;
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE t_p56991462_quantum_explorer_1.orders ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP;