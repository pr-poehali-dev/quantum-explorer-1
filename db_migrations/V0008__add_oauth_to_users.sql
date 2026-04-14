ALTER TABLE t_p56991462_quantum_explorer_1.users
  ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(32) NULL,
  ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(128) NULL;

CREATE UNIQUE INDEX IF NOT EXISTS users_oauth_idx
  ON t_p56991462_quantum_explorer_1.users(oauth_provider, oauth_id)
  WHERE oauth_provider IS NOT NULL AND oauth_id IS NOT NULL;