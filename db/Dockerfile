# Use the official MySQL 8 image
FROM mysql:8

# Set the environment variable to avoid tzdata warnings
ENV MYSQL_INITDB_SKIP_TZINFO 1

# Copy MySQL configuration file
COPY my.cnf /etc/mysql/my.cnf

# Ensure correct permissions
RUN chmod 644 /etc/mysql/my.cnf && chown root:root /etc/mysql/my.cnf

# Copy the init SQL script to the container
COPY init.sql /docker-entrypoint-initdb.d/