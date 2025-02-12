@echo off
echo Starting MySQL and phpMyAdmin Docker containers...
docker-compose up -d db phpmyadmin
echo MySQL and phpMyAdmin are running! ✅
echo Access phpMyAdmin at: http://localhost:8080
pause
