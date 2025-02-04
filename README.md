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
│   ├── Dockerfile
│   ├── init.sql
│   ├── job_storage.py
│   └── my.cnf
├── gui/                        # Graphical User Interface components
│   ├── __init__.py
│   └── my_gui.py
├── utils/                      # Utility functions and configuration files
│   ├── __init__.py
│   └── env_config.py
├── .env                        # Environment variables file
├── grow-hire.iml               
├── main.py                     # Application entry point
├── build.bat                   # Build script 
├── requirements.txt
└── start_db.bat                
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
6. **GUI**: Provides a user-friendly interface to manage job search parameters

---

## Getting Started

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ItayOlivcovitz/GrowHire
   cd GrowHire
   ```

2. **Set Up Environment Variables**:

   - Create a `.env` file in the project root with the following variables:

```bash
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
OPENAI_API_KEY=
RESUME_PATH=
```

You can also add any additional environment variables (e.g., database credentials) as needed.

3. **Build the Database Container** (if necessary):

   - Run `build.bat` (Windows) or create your own build script for other systems, which specifically builds the Docker image for the MySQL database.

4. **Start the Database**:

   - Ensure Docker is installed and running.
   - Run `start_db.bat` (for Windows) to spin up a MySQL container using the `db/Dockerfile`.
   - Or use the command line: `docker build -t growhire-db db/` then `docker run -d -p 3306:3306 --name growhire-db growhire-db`

5. **Install Python Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

6. **Run the Application**:

   ```bash
   python main.py
   ```

---

## Usage

1. **Configuring LinkedIn Automation**: Fill your `.env` file with your LinkedIn credentials \
   and OpenAI API key .
2. **Add Resume** : add resume.pdf to the resume folder (optional - do it here or every time in the GUI)
3. **Run the application:**  python main.py
4. **Fill filters:** fill in your search filters to refine the LinkedIn jobs you want to match against.&#x20;
5. **Click  🌐 Open LinkedIn Login:** The application will open Chrome to the LinkedIn login page and attempt to connect. If there's a CAPTCHA, just solve it manually and continue.
6. **Click 🔍 Search Jobs**: That will open the job page with the filters.
7. **Set the number of pages you want to seach and Click 🔎 Start Scan for New Jobs**

---

## Contribution

Contributions are always welcome! Please open an issue or submit a pull request for any changes.

---

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use it as you see fit.

