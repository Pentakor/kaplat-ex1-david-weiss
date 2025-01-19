CREATE TABLE genre (
id SERIAL PRIMARY KEY,
name VARCHAR(255) NOT NULL
);

CREATE TABLE book (
rawid SERIAL PRIMARY KEY,
title VARCHAR(255) NOT NULL,
author VARCHAR(255) NOT NULL,
year INTEGER,
price INTEGER
);

CREATE TABLE book_genre (
book_rawid INTEGER,
genre_id INTEGER,
PRIMARY KEY (book_rawid, genre_id),
FOREIGN KEY (book_rawid) REFERENCES book(rawid),
FOREIGN KEY (genre_id) REFERENCES genre(id)
);

INSERT INTO genre (name)
VALUES 
    ('SCI_FI'),
    ('NOVEL'),
    ('HISTORY'),
    ('MANGA'),
    ('ROMANCE'),
    ('PROFESSIONAL');