CREATE DATABASE IF NOT EXISTS flaskdb;
USE flaskdb;

CREATE TABLE IF NOT EXISTS tbl_user (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(45) NULL,
    user_username VARCHAR(45) NULL,
    user_password VARCHAR(255) NULL,
    PRIMARY KEY (user_id)
);

DELIMITER //
CREATE PROCEDURE sp_createUser(
    IN p_name VARCHAR(45),
    IN p_username VARCHAR(45),
    IN p_password VARCHAR(255)
)
BEGIN
    INSERT INTO tbl_user (user_name, user_username, user_password)
    VALUES (p_name, p_username, p_password);
END //

CREATE PROCEDURE sp_validateLogin(
    IN p_username VARCHAR(45)
)
BEGIN
    SELECT * FROM tbl_user WHERE user_username = p_username;
END //
DELIMITER ;