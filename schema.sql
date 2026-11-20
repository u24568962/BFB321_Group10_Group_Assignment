-- Create tables for users, drivers, trucks, the goods_categories, lanes, admin_windows, crpossings (trips throught he border), crossing_goods (the goods transported in a crossing) and status_events --

-- users table --
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role varchar(20) NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_role CHECK (role IN ('canopy1', 'immigration', 'canopy2', 'admin'))    
);

-- Drivers table to store driver information--
CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    passport_number VARCHAR(20) NOT NULL UNIQUE,
    nationality VARCHAR(60) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    licence_number VARCHAR(30) NOT NULL UNIQUE,
    licence_expiry DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Trucks --
CREATE TABLE IF NOT EXISTS trucks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(15) NOT NULL UNIQUE,
    country_registration VARCHAR(60) NOT NULL,
    make_model VARCHAR(60) NULL, year SMALLINT NULL,
    trailer_registration VARCHAR(15) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_trucks_year CHECK (year IS NULL OR year BETWEEN 1950 AND 2100)
);

-- Goods categories --
CREATE TABLE IF NOT EXISTS goods_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE, -- This matches the checkbox name
    label VARCHAR(80) NOT NULL,           
    extra_minutes DECIMAL(4,1) NOT NULL DEFAULT 0, -- model input
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_goods_minutes CHECK (extra_minutes BETWEEN 0 AND 60)
);

-- parking lanes --
CREATE TABLE IF NOT EXISTS lanes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lane_number INT NOT NULL UNIQUE,
    capacity INT NOT NULL DEFAULT 5,
    active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_lanes_capacity CHECK (capacity BETWEEN 1 AND 20)
);

-- admin windows for processing --
CREATE TABLE IF NOT EXISTS admin_windows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    window_number INT NOT NULL UNIQUE,
    is_open TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- trucks crossing the border --
CREATE TABLE IF NOT EXISTS crossings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    manifest_reference VARCHAR(30) NOT NULL UNIQUE,
    driver_id INT NOT NULL,
    truck_id INT NOT NULL,
    crossing_status VARCHAR(20) NOT NULL DEFAULT 'registered',
    other_goods VARCHAR(255) NULL,
    lane_id INT NULL,
    window_id INT NULL,
    processing_minutes DECIMAL(5,1) NULL,   -- model output
    predicted_wait_minutes DECIMAL(6,1) NULL,   -- model output
    registered_by INT NULL,
    arrived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    allocated_at DATETIME NULL,
    immigration_started_at DATETIME NULL,
    cleared_at DATETIME NULL,
    exited_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_crossings_driver FOREIGN KEY (driver_id) REFERENCES drivers (id),
    CONSTRAINT fk_crossings_truck FOREIGN KEY (truck_id) REFERENCES trucks (id),
    CONSTRAINT fk_crossings_lane FOREIGN KEY (lane_id) REFERENCES lanes (id),
    CONSTRAINT fk_crossings_window FOREIGN KEY (window_id) REFERENCES admin_windows (id),
    CONSTRAINT fk_crossings_user FOREIGN KEY (registered_by) REFERENCES users (id),
    CONSTRAINT chk_crossings_status CHECK (crossing_status IN ('registered', 'goods_declared', 'allocated','at_immigration', 'cleared', 'exited')),
    INDEX idx_crossings_status (crossing_status),
    INDEX idx_crossings_lane_status (lane_id, crossing_status),-- lane occupancy
    INDEX idx_crossings_window_status (window_id, crossing_status),-- immigration board
    INDEX idx_crossings_arrived (arrived_at)-- KPIs by day / hour
);

-- goods that cross --
CREATE TABLE IF NOT EXISTS crossing_goods (
    crossing_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (crossing_id, category_id),
    CONSTRAINT fk_cg_crossing FOREIGN KEY (crossing_id) REFERENCES crossings (id) ON DELETE CASCADE,
    CONSTRAINT fk_cg_category FOREIGN KEY (category_id) REFERENCES goods_categories (id)
);

-- status events for tracking the status changes of crossings --
CREATE TABLE IF NOT EXISTS status_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crossing_id INT NOT NULL,
    from_status VARCHAR(20) NULL,
    to_status VARCHAR(20) NOT NULL,
    user_id INT NULL,
    note VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_events_crossing FOREIGN KEY (crossing_id) REFERENCES crossings (id) ON DELETE CASCADE,
    CONSTRAINT fk_events_user FOREIGN KEY (user_id) REFERENCES users (id),
    INDEX idx_events_crossing_time (crossing_id, created_at)
);