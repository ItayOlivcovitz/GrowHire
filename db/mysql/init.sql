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

CREATE TABLE IF NOT EXISTS linkedin_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(255) UNIQUE NOT NULL,  -- Unique identifier for the post
    publisher_url TEXT,  -- URL of the post's publisher (nullable)
    publish_date TIMESTAMP NULL,  -- Publish date (nullable)
    post_text TEXT NOT NULL,  -- Full text content of the post
    links JSON,  -- Store links as JSON array
    emails JSON,  -- Store extracted emails as JSON array
    keyword_found VARCHAR(255) DEFAULT NULL,  -- Holds a string indicating the found keyword(s)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Auto-generated timestamp
);


