-- Create a new database
CREATE DATABASE IF NOT EXISTS growhire;

-- Use the newly created database
USE growhire;

-- Create a table to store job descriptions
CREATE TABLE IF NOT EXISTS job_descriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    job_location VARCHAR(255) NOT NULL,
    job_url TEXT NOT NULL,  
    connections INT DEFAULT 0,
    score INT DEFAULT 0,
    job_description TEXT NOT NULL,
    chat_gpt_response TEXT,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
