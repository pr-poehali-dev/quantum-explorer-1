ALTER TABLE t_p56991462_quantum_explorer_1.users
  ADD COLUMN IF NOT EXISTS telegram_id BIGINT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS users_telegram_id_idx
  ON t_p56991462_quantum_explorer_1.users(telegram_id)
  WHERE telegram_id IS NOT NULL;