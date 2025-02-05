# GrowHire

A LinkedIn automation tool that allows you to scan a large number of jobs on LinkedIn, compare your resume with the job descriptions, and get an AI-driven analysis along with a match score (in percentage). This project uses a Docker-based MySQL container to store job descriptions, AI responses, and other data.

---

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contribution](#contribution)
- [License](#license)

---

## Overview

GrowHire leverages:

- LinkedIn automation for job searching.
- An AI component (OpenAI's ChatGPT) to provide a detailed analysis of each job description.
- A match score in percentage to gauge how closely your resume matches the job.
- Docker-based MySQL for reliable and portable database management.
- Web-based GUI accessible via `http://localhost:6080/vnc.html`.

---

## Directory Structure

```plaintext
GrowHire/
├── services/                   # Core business logic and integrations
│   ├── __init__.py
│   ├── chatgpt/                # ChatGPT API integration
│   │   ├── __init__.py
│   │   └── chat_gpt.py
│   ├── jobScraper/             # Job scraping functionality
│   │   ├── __init__.py
│   │   └── job_scraper.py
│   ├── linkedin/               # LinkedIn automation tasks
│   │   ├── __init__.py
│   │   └── linkedin_navigator.py
│   └── pdfReader/              # PDF reading functionality
│       ├── __init__.py
│       └── pdf_reader.py
├── db/                         # Database-related files and configurations
│   ├── __init__.py
│   ├── init.sql
│   ├── job_storage.py
│   └── my.cnf
├── gui/                        # Graphical User Interface components
│   ├── __init__.py
│   └── my_gui.py
├── utils/                      # Utility functions and configuration files
│   ├── __init__.py
│   └── env_config.py
├── .env                        # Environment variables file (populate this)
├── grow-hire.iml               
├── main.py                     # Application entry point
├── build_docker_compose.bat     # Build script for Docker Compose
├── docker_compose_up.bat        # Run script for Docker Compose
├── requirements.txt               
```

### Key folders:

- **services**: Contains all the main business logic and external integrations (ChatGPT, job scraping, LinkedIn tasks, PDF reading).
- **db**: Holds database-related files, including the Dockerfile, initial SQL scripts, and configurations for MySQL.
- **gui**: GUI components for user interactions.
- **utils**: Miscellaneous utility functions and configuration loading scripts.

---

## Features

1. **LinkedIn Automation**: Automates job searches on LinkedIn, allowing you to fetch job data in bulk.
2. **AI Analysis (ChatGPT)**: Leverages the OpenAI ChatGPT model to provide detailed insights into each job description.
3. **Resume Matching**: Compares your resume with each job posting, returning a match score (in percentage).
4. **Dockerized MySQL**: Spins up a MySQL container for easy deployment and portability.
5. **Data Storage**: Stores all job descriptions, AI responses, and match scores in the MySQL database.
6. **GUI**: Provides a user-friendly interface to manage job search parameters, accessible at `http://localhost:6080/vnc.html`.

---

## Getting Started

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ItayOlivcovitz/GrowHire
   cd GrowHire
   ```

2. **Set Up Environment Variables**:

   - Populate the `.env` file in the project root with the following variables:

   ```bash
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   OPENAI_API_KEY=your_openai_api_key
   RESUME_PATH=/app/resume/Resume.pdf
   ```

3. **Build the Docker Containers**:

   - Run `build_docker_compose.bat` (for Windows) or execute the following command manually:

     ```bash
     docker-compose build
     ```

4. **Start the Application**:

   - Run `docker_compose_up.bat` (for Windows) or execute:

     ```bash
     docker-compose up -d
     ```

5. **Access the Application**:

   - Open `http://localhost:6080/vnc.html` in your browser to access the GUI.

6. **Install Python Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

7. **Run the Application Manually (if needed)**:

   ```bash
   python main.py
   ```

---

## Usage

1. **Configuring LinkedIn Automation**: Populate the `.env` file with your LinkedIn credentials and OpenAI API key.
2. **Add Resume**: Place your resume file (`Resume.pdf`) in the `resume` folder.
3. **Run the application**: Start the program using the GUI or via `main.py`.
4. **Fill Search Filters**: Enter your search criteria for job matching.
5. **Login to LinkedIn**: Click 🌐 **Open LinkedIn Login**, solve any CAPTCHA manually if needed.
6. **Start Job Search**: Click 🔍 **Search Jobs** to find job listings.
7. **Scan Job Listings**: Set the number of pages and click 🔎 **Start Scan for New Jobs**.

---

## Contribution

Contributions are always welcome! Please open an issue or submit a pull request for any changes.

---

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use it as you see fit.
