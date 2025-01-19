FROM postgres:latest

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgrespass
ENV POSTGRES_DB=books_db

COPY init.sql /docker-entrypoint-initdb.d/
