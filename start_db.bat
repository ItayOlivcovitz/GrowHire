@echo off
echo Starting MySQL using Docker Compose...

cd /d "%~dp0db"
docker run -d --name my-mysql-container -p 3306:3306 -v /etc/localtime:/etc/localtime:ro -v /etc/timezone:/etc/timezone:ro -e TZ=Asia/Jerusalem -e MYSQL_ROOT_PASSWORD=root my-mysql-image


echo ✅ MySQL container started successfully!

:: Verify time inside the container
echo Checking time inside the MySQL container...
docker exec -it my-mysql-container date
docker exec -it my-mysql-container mysql -u root -proot -e "SELECT NOW();"

pause
