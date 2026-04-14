DROP INDEX IF EXISTS t_p56991462_quantum_explorer_1.cart_items_session_product_idx;

CREATE UNIQUE INDEX cart_items_session_product_idx
  ON t_p56991462_quantum_explorer_1.cart_items(session_id, product_id);