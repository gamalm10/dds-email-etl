FROM mariadb:11

# Schema migrations run automatically on first boot with an empty data volume.
COPY migrations /docker-entrypoint-initdb.d
