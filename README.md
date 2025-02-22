A LinkedIn automation tool that allows you to scan a large number of jobs on LinkedIn, compare your resume with the job descriptions, and get an AI-driven analysis along with a match score (in percentage). This project uses a Docker-based MySQL container to store job descriptions, AI responses, and other data.

Project site: [GrowHire](https://growhire.up.railway.app/)

---

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Features](#features)
- [Getting Started - OpenAPI Key](#getting-started---openapi-key)
- [Getting Started - ChatService](#getting-started---chatservice)
- [Run Using Docker](#run-using-docker)
- [Usage](#usage)
- [Contribution](#contribution)
- [License](#license)

---

## Overview

GrowHire leverages:

- Feed Scroller that saves posts with keywords in it.
- LinkedIn automation for job searching.
- An AI component (OpenAI's ChatGPT) to provide a detailed analysis of each job description.
- A match score in percentage to gauge how closely your resume matches the job.
- Docker-based MySQL for reliable and portable database management.

---

## Directory Structure

```plaintext
GrowHire/
├── app/
│   ├── gui/
│   │   ├── workers/         # GUI worker components
│   │   └── panels/          # GUI panels/components
│   ├── services/            # Core business logic and integrations
│   │   ├── chatService/     # Chat service functionality
│   │   ├── feedScraper/     # Web scraping for job feeds
│   │   ├── jobScraper/      # Job scraping functionality
│   │   ├── linkedinNavigator/ # LinkedIn navigation automation
│   │   ├── pdfReader/       # PDF resume reader
│   │   └── getConnected/    # "Get Connected" functionality
│   └── utils/               # Utility functions and configuration files
│       ├── env_config       # Environment configuration
│       ├── keywords.txt     # Keywords file
│       └── prompt_template.txt  # Prompt template file
├── db/                      # Database-related files and configurations
│   ├── mysql/               # MySQL-related files
│   ├── sqlite/              # SQLite-related files
│   ├── init.sql
│   ├── job_storage          # Database access module
│   └── my.cnf
├── docker/                  # Docker configurations and files
├── resume/                  # Resume assets or related functionality
├── .env                     # Environment variables file (populate this)
├── grow-hire.iml
├── main.py                  # Application entry point
├── requirements.txt                
```

---

## Features

1. **LinkedIn Automation**: Automates job searches on LinkedIn, allowing you to fetch job data in bulk.
2. **AI Analysis (ChatGPT)**: Leverages the OpenAI ChatGPT model to provide detailed insights into each job description.
3. **Resume Matching**: Compares your resume with each job posting, returning a match score (in percentage).
4. **Dockerized MySQL**: Spins up a MySQL container for easy deployment and portability.
5. **Data Storage**: Stores all job descriptions, AI responses, and match scores in the MySQL database.
6. **GUI**: Provides a user-friendly interface to manage job search parameters.

---

## Getting Started - OpenAPI Key

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
   DATABASE_URL=sqlite:///growhire.db
   AI_CHAT_SERVICE_URL= #Ignore - keep empty
   ```

3. **Install Python Dependencies:**  

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Application**:

   ```bash
   python main.py
   ```

---

## Getting Started - ChatService

If you don't have an OpenAI Key, contact me and I will provide you with the `AI_CHAT_SERVICE_URL`.

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ItayOlivcovitz/GrowHire
   cd GrowHire
   ```

2. **Set Up Environment Variables**:

   ```bash
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   OPENAI_API_KEY= #Ignore - keep empty
   RESUME_PATH=/app/resume/Resume.pdf
   DATABASE_URL= sqlite:///growhire.db
   AI_CHAT_SERVICE_URL= the provided URL here
   ```

3. **Install Python Dependencies:**  

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the Application:**  

```bash
python main.py
```

---

## Run Using Docker

If you don't have an OpenAI Key, contact me and I will provide you with the `AI_CHAT_SERVICE_URL`.

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/ItayOlivcovitz/GrowHire
   cd GrowHire
   ```

2. **Set Up Environment Variables**:

   ```bash
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   OPENAI_API_KEY= #Ignore - keep empty
   RESUME_PATH=/app/resume/Resume.pdf
   DATABASE_URL= mysql://root:root@localhost:3306/growhire
   AI_CHAT_SERVICE_URL= the provided URL here
   ```

3. **Build Docker image -** run `docker/build_docker_compose.bat`

4. **Start Docker Containers -** run `docker/docker_compose_up.bat`

---

## Usage

- **Disclaimer**: This tool is provided as-is, and I am not responsible for any consequences resulting from its use. Users should ensure they comply with LinkedIn's policies and terms of service when using GrowHire.

- **Chat Service**: The Chat Service is a locally hosted application on my personal computer. Its purpose is to allow users to utilize GrowHire's AI-driven job analysis features **without** requiring their own OpenAI API key.

---

## Contribution

Contributions are always welcome! Please open an issue or submit a pull request for any changes.

---

## License

This project is licensed under the [MIT License](LICENSE). Feel free to use it as you see fit.
