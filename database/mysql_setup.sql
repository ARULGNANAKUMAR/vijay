-- FloatChat ARGO Database Setup Script
-- MySQL/MariaDB Schema

-- Create database
CREATE DATABASE IF NOT EXISTS floatchat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (change password in production)
CREATE USER IF NOT EXISTS 'floatchat_user'@'localhost' IDENTIFIED BY 'secure_password_123';
GRANT ALL PRIVILEGES ON floatchat.* TO 'floatchat_user'@'localhost';
FLUSH PRIVILEGES;

USE floatchat;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- ARGO floats table
CREATE TABLE IF NOT EXISTS argo_floats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    float_id VARCHAR(20) NOT NULL UNIQUE,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    deployment_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    last_profile DATE,
    profiles_count INT DEFAULT 0,
    region VARCHAR(50),
    battery_level INT DEFAULT 100,
    next_maintenance DATE,
    data_quality VARCHAR(20) DEFAULT 'good',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_float_id (float_id),
    INDEX idx_location (latitude, longitude),
    INDEX idx_status (status),
    INDEX idx_region (region),
    CONSTRAINT chk_battery CHECK (battery_level >= 0 AND battery_level <= 100),
    CONSTRAINT chk_status CHECK (status IN ('active', 'inactive', 'maintenance', 'lost'))
);

-- Ocean profiles table
CREATE TABLE IF NOT EXISTS ocean_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    float_id VARCHAR(20) NOT NULL,
    profile_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    depth DECIMAL(8, 2),
    temperature DECIMAL(6, 3),
    salinity DECIMAL(6, 3),
    pressure DECIMAL(8, 2),
    oxygen DECIMAL(8, 3),
    quality_flag VARCHAR(5) DEFAULT 'GOOD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_float_profile (float_id, profile_date),
    INDEX idx_location_time (latitude, longitude, profile_date),
    INDEX idx_depth (depth),
    INDEX idx_quality (quality_flag),
    FOREIGN KEY (float_id) REFERENCES argo_floats(float_id) ON DELETE CASCADE
);

-- Insert sample data
INSERT IGNORE INTO users (username, email, password_hash, role, full_name) VALUES
('admin', 'admin@floatchat.com', 'pbkdf2:sha256:260000$QjGVEcXIYQDVGktn$e8b7a7b6d5c9b3a2f1e4d7c0f3b6e9d2c5b8e1f4a7d0c3b6e9d2f5a8b1e4c7f0', 'admin', 'System Administrator'),
('user', 'user@floatchat.com', 'pbkdf2:sha256:260000$YZjKLnWqEcUdGvhs$b8e1f4c7d0a3b6e9d2f5a8c1e4d7f0b3b6e9d2c5f8b1e4a7d0c3b6f9e2d5a8c1', 'user', 'Marine Researcher');

-- Insert sample ARGO floats
INSERT IGNORE INTO argo_floats (float_id, latitude, longitude, deployment_date, status, region, battery_level, data_quality) VALUES
('2901623', -10.5, 67.8, '2023-03-15', 'active', 'Indian Ocean', 87, 'good'),
('2901624', -15.2, 72.1, '2023-03-20', 'active', 'Indian Ocean', 92, 'excellent'),
('2901625', -8.7, 65.3, '2023-04-02', 'active', 'Indian Ocean', 78, 'good'),
('2901626', -12.8, 70.5, '2023-02-28', 'maintenance', 'Indian Ocean', 45, 'poor'),
('2901627', -6.2, 68.9, '2023-05-10', 'active', 'Indian Ocean', 89, 'excellent');

-- Insert sample ocean profiles
INSERT IGNORE INTO ocean_profiles (float_id, latitude, longitude, depth, temperature, salinity, pressure, oxygen) VALUES
('2901623', -10.52, 67.83, 5, 28.5, 35.1, 5.1, 215.4),
('2901623', -10.52, 67.83, 10, 28.3, 35.2, 10.2, 214.8),
('2901623', -10.52, 67.83, 25, 27.8, 35.3, 25.5, 212.1),
('2901623', -10.52, 67.83, 50, 26.2, 35.4, 51.0, 198.7),
('2901623', -10.52, 67.83, 100, 22.1, 35.2, 102.3, 165.2),
('2901624', -15.18, 72.05, 5, 27.8, 35.3, 5.1, 218.2),
('2901624', -15.18, 72.05, 10, 27.6, 35.4, 10.1, 217.5),
('2901624', -15.18, 72.05, 25, 27.1, 35.5, 25.3, 214.8),
('2901624', -15.18, 72.05, 50, 25.8, 35.6, 50.8, 201.3),
('2901624', -15.18, 72.05, 100, 21.5, 35.3, 101.9, 168.7);

-- Create views for common queries
CREATE OR REPLACE VIEW active_floats AS
SELECT f.*, COUNT(p.id) as recent_profiles
FROM argo_floats f
LEFT JOIN ocean_profiles p ON f.float_id = p.float_id 
    AND p.profile_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
WHERE f.status = 'active'
GROUP BY f.id;

CREATE OR REPLACE VIEW latest_profiles AS
SELECT p.*
FROM ocean_profiles p
INNER JOIN (
    SELECT float_id, MAX(profile_date) as max_date
    FROM ocean_profiles
    GROUP BY float_id
) latest ON p.float_id = latest.float_id AND p.profile_date = latest.max_date;

-- Create stored procedures for common operations
DELIMITER //

CREATE PROCEDURE GetFloatProfiles(IN float_id_param VARCHAR(20), IN limit_count INT)
BEGIN
    SELECT * FROM ocean_profiles 
    WHERE float_id = float_id_param 
    ORDER BY profile_date DESC 
    LIMIT limit_count;
END//

CREATE PROCEDURE GetFloatsInRegion(IN min_lat DECIMAL(10,6), IN max_lat DECIMAL(10,6), 
                                   IN min_lon DECIMAL(10,6), IN max_lon DECIMAL(10,6))
BEGIN
    SELECT * FROM argo_floats 
    WHERE latitude BETWEEN min_lat AND max_lat 
    AND longitude BETWEEN min_lon AND max_lon 
    AND status = 'active';
END//

DELIMITER ;

-- Create triggers for audit logging
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50),
    operation VARCHAR(10),
    old_values JSON,
    new_values JSON,
    user_id INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //

CREATE TRIGGER argo_floats_audit AFTER UPDATE ON argo_floats
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, operation, old_values, new_values, timestamp)
    VALUES ('argo_floats', 'UPDATE', 
            JSON_OBJECT('id', OLD.id, 'status', OLD.status, 'battery_level', OLD.battery_level),
            JSON_OBJECT('id', NEW.id, 'status', NEW.status, 'battery_level', NEW.battery_level),
            NOW());
END//

DELIMITER ;

SHOW TABLES;
SELECT 'Database setup completed successfully!' as message;
