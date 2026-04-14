ALTER TABLE t_p56991462_quantum_explorer_1.cart_items
  ADD COLUMN IF NOT EXISTS session_id VARCHAR(64);

ALTER TABLE t_p56991462_quantum_explorer_1.cart_items
  DROP CONSTRAINT IF EXISTS cart_items_user_id_product_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS cart_items_session_product_idx
  ON t_p56991462_quantum_explorer_1.cart_items(session_id, product_id)
  WHERE session_id IS NOT NULL;