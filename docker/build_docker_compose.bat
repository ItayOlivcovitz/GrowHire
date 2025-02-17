@echo off
cd /d %~dp0
echo Building Docker containers...
docker-compose build
echo Done!
pause
