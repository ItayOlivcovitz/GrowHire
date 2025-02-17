@echo off
cd /d %~dp0
echo Starting Docker containers...
docker-compose up -d
echo Containers are running!
pause
