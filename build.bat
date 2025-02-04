@echo off
echo Starting MySQL using Docker Compose...

cd /d "%~dp0db"
docker build -t my-mysql-image .


echo ✅ MySQL container started successfully!
pause
