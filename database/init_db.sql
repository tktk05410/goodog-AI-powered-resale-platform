-- 校园二手交易平台数据库初始化脚本
-- 数据库名: goodog_date
-- 端口: 3306
-- 用户: root

CREATE DATABASE IF NOT EXISTS goodog_date DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE goodog_date;

-- 用户表
CREATE TABLE IF NOT EXISTS `user` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(64) NOT NULL,
    `student_id` VARCHAR(20) UNIQUE,
    `credit_score` INT DEFAULT 100,
    `face_encoding` BLOB,
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`),
    INDEX `idx_student_id` (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 商品表
CREATE TABLE IF NOT EXISTS `product` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(100) NOT NULL,
    `description` TEXT NOT NULL,
    `type` ENUM('sell', 'buy') NOT NULL,
    `price` DECIMAL(10, 2),
    `image_path` VARCHAR(255),
    `user_id` INT NOT NULL,
    `status` ENUM('on', 'off', 'sold') DEFAULT 'on',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    INDEX `idx_title` (`title`(50)),
    INDEX `idx_type` (`type`),
    INDEX `idx_status` (`status`),
    INDEX `idx_user_id` (`user_id`),
    FULLTEXT INDEX `ft_title_desc` (`title`, `description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 交易表
CREATE TABLE IF NOT EXISTS `transaction` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `product_id` INT NOT NULL,
    `buyer_id` INT NOT NULL,
    `seller_id` INT NOT NULL,
    `state` ENUM('pending', 'paid', 'done', 'canceled') DEFAULT 'pending',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`buyer_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`seller_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    INDEX `idx_product_id` (`product_id`),
    INDEX `idx_buyer_id` (`buyer_id`),
    INDEX `idx_seller_id` (`seller_id`),
    INDEX `idx_state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 消息表
CREATE TABLE IF NOT EXISTS `message` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `from_user` INT NOT NULL,
    `to_user` INT NOT NULL,
    `content` TEXT NOT NULL,
    `is_read` BOOLEAN DEFAULT FALSE,
    `ai_summary` VARCHAR(200),
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`from_user`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`to_user`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    INDEX `idx_from_user` (`from_user`),
    INDEX `idx_to_user` (`to_user`),
    INDEX `idx_is_read` (`is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 系统日志表
CREATE TABLE IF NOT EXISTS `system_log` (
    `log_id` BIGINT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT,
    `action` VARCHAR(100) NOT NULL,
    `detail` JSON,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_action` (`action`),
    INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 标签表
CREATE TABLE IF NOT EXISTS `tag` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL UNIQUE,
    `color` VARCHAR(20) DEFAULT '#409eff',
    `is_ai_generated` BOOLEAN DEFAULT FALSE,
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 商品标签关联表
CREATE TABLE IF NOT EXISTS `product_tag` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `product_id` INT NOT NULL,
    `tag_id` INT NOT NULL,
    `is_ai_generated` BOOLEAN DEFAULT FALSE,
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tag_id`) REFERENCES `tag`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `uq_product_tag` (`product_id`, `tag_id`),
    INDEX `idx_product_id` (`product_id`),
    INDEX `idx_tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;