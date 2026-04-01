CREATE TABLE IF NOT EXISTS t_p56991462_quantum_explorer_1.managers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);