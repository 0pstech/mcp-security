-- Create a sample table for users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a default user
INSERT INTO users (username, password, email) VALUES
('admin', 'adminpass', 'admin@example.com')
ON DUPLICATE KEY UPDATE username=username; 