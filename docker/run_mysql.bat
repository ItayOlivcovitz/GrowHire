@echo off
echo Starting MySQL Docker containers...
docker-compose up -d db 
echo MySQL and phpMyAdmin are running! ✅

pause
