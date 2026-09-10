# syntax=docker/dockerfile:1
FROM mysql:8.0

# Runs automatically on first boot with an empty data volume
COPY init/ /docker-entrypoint-initdb.d/

EXPOSE 3306