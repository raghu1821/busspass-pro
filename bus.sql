-- 1. Route Table (Lookup table for bus paths and fares)
CREATE TABLE `route` (
  `route_id` INT NOT NULL AUTO_INCREMENT,
  `source` VARCHAR(100) DEFAULT NULL,
  `destination` VARCHAR(100) DEFAULT NULL,
  `base_fare` DECIMAL(10,2) DEFAULT NULL,
  PRIMARY KEY (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Passenger Table (Stores registered accounts and document status)
CREATE TABLE `passenger` (
  `passenger_id` INT NOT NULL AUTO_INCREMENT,
  `full_name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) DEFAULT NULL,
  `address` TEXT,
  `category` ENUM('Student','Employee','Senior Citizen','General','Physically Challenged') NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `photo` LONGTEXT,              -- Base64 Profile image
  `doc_proof` LONGTEXT,          -- Base64 Document ID proof
  `doc_status` VARCHAR(20) DEFAULT 'Not Uploaded',
  PRIMARY KEY (`passenger_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Pass Application Table (Stores requests awaiting review)
CREATE TABLE `pass_application` (
  `application_id` INT NOT NULL AUTO_INCREMENT,
  `passenger_name` VARCHAR(100) DEFAULT NULL,
  `route_id` INT DEFAULT NULL,
  `pass_type` VARCHAR(50) DEFAULT NULL,
  `duration` INT DEFAULT NULL,
  `status` VARCHAR(50) DEFAULT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`application_id`),
  KEY `route_id` (`route_id`),
  CONSTRAINT `pass_application_ibfk_1` FOREIGN KEY (`route_id`) REFERENCES `route` (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Pass Table (Stores active/valid passes with QR Code references)
CREATE TABLE `pass` (
  `pass_id` INT NOT NULL AUTO_INCREMENT,
  `passenger_name` VARCHAR(100) DEFAULT NULL,
  `pass_type` VARCHAR(50) DEFAULT NULL,
  `valid_until` DATE DEFAULT NULL,
  `status` VARCHAR(50) DEFAULT NULL,
  `qr_code` LONGTEXT,            -- Base64/File QR code string
  PRIMARY KEY (`pass_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Feedback Table (Stores passenger suggestions/issues)
CREATE TABLE `feedback` (
  `feedback_id` INT NOT NULL AUTO_INCREMENT,
  `passenger_name` VARCHAR(100) DEFAULT NULL,
  `message` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `topic` VARCHAR(50) DEFAULT 'General',
  PRIMARY KEY (`feedback_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Admin Table (Stores backend administrator credentials)
CREATE TABLE `admin` (
  `admin_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) DEFAULT NULL,
  `password` VARCHAR(100) DEFAULT NULL,
  PRIMARY KEY (`admin_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default admin account (Username: admin, Password: admin123)
INSERT INTO `admin` (`username`, `password`) VALUES ('admin', 'admin123');

use buspassdb;

-- View all registered passengers (and check verification document upload status)
SELECT * FROM passenger;

-- View all pass applications (and verify pending/approved statuses)
SELECT * FROM pass_application;

-- View all generated active and expired passes (and their validity dates)
SELECT * FROM pass;





-- 1. Switch to your database
USE buspassdb;

-- 2. Clear old mock applications from January to May
DELETE FROM pass_application WHERE created_at < '2026-06-01';

-- 3. Clear old mock passes from January to May
-- (This ensures only your active June passes are counted)
DELETE FROM pass WHERE valid_until < '2026-07-01';

-- 4. (Optional) Clear old passenger accounts that you don't need
DELETE FROM passenger WHERE email IN ('m123@gmail.com', 'r123@gmail.com', 'ra123@gmail.com', 'si123@gmail.com', 'sha123@gmail.com');

-- View all bus routes and their corresponding base fares
SELECT * FROM route;

-- View all passenger feedback submissions
SELECT * FROM feedback;

-- View all administrators
SELECT * FROM admin;

UPDATE pass_application SET status = 'Approved' WHERE application_id = 12;
UPDATE pass SET status = 'Expired' WHERE passenger_name = 'Demo Student';
UPDATE route SET base_fare = 35.00 WHERE source = 'Majestic' AND destination = 'Kengeri';

UPDATE pass_application SET status = 'Approved' 
WHERE passenger_name = 'Demo Student' AND status = 'Pending';

UPDATE passenger SET doc_status = 'Verified' WHERE email = 'demo@gmail.com';

UPDATE pass_application SET status = 'Approved' WHERE application_id = 12;

SELECT passenger_id, full_name, email, phone, category, doc_status FROM passenger;