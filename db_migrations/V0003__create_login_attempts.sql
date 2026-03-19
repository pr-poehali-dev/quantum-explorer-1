CREATE TABLE IF NOT EXISTS t_p56991462_quantum_explorer_1.login_attempts (
    id SERIAL PRIMARY KEY,
    ip TEXT NOT NULL,
    email TEXT NOT NULL,
    attempted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON t_p56991462_quantum_explorer_1.login_attempts (ip, attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON t_p56991462_quantum_explorer_1.login_attempts (email, attempted_at);