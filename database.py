from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
from pymongo import MongoClient
from env_variables import *

# Establish MongoDB connection
mongo_client = MongoClient(MONGO_DB_URL)
mongo_db = mongo_client["library"]
books_col = mongo_db["books"]

# Establish PostgreSQL connection
engine = create_engine(PG_DATABASE_URL)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


class Genre(Base):
    # Genre ORM for SQL DB
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class Book(Base):
    # Book ORM for SQL DB
    __tablename__ = 'book'

    rawid = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    year = Column(Integer)
    price = Column(Integer)


class BookGenre(Base):
    # Book-genre connection Table ORM for SQL DB
    __tablename__ = 'book_genre'

    book_rawid = Column(Integer, ForeignKey('book.rawid'), primary_key=True)
    genre_id = Column(Integer, ForeignKey('genre.id'), primary_key=True)


class DataBaseHelper:
    # Includes all the methods for Data Bases handling
    @staticmethod
    def book_to_dict(book):
        # Converts the ORM type with the genres from Genre table to a dictionary with the relevant information
        query = (
            select(Genre.name)
            .join(BookGenre, Genre.id == BookGenre.genre_id)
            .where(BookGenre.book_rawid == book.rawid)
        )

        # Execute the query and fetch all results
        genre_names = session.execute(query).scalars().all()

        return {
            "id": book.rawid,
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "price": book.price,
            "genres": genre_names
        }

    @staticmethod
    def genres_match(i_genres):
        # Checks if the genres in the list are present in the PosgreSQL DB
        genres = [genre.name for genre in session.query(Genre.name).all()]
        for item in i_genres:
            if item not in genres:
                return False
        return True

    @staticmethod
    def add_book(book, genres):
        # Adds the book information to the databases
        session.add(book)

        # Adds the genres to the connection table
        for genre_name in genres:
            genre = session.query(Genre).filter_by(name=genre_name).first()
            book_genre = BookGenre(book_rawid=book.rawid, genre_id=genre.id)
            session.add(book_genre)

        # Adds the book to PostgreSQL
        session.commit()

        print(book.rawid)
        mongo_dict = {
            "rawid": book.rawid,
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "price": book.price,
            "genres": genres
        }

        # Adds the book to mongodb
        books_col.insert_one(mongo_dict)

    @staticmethod
    def add_book_to_mongo(rawid):
        # Adds the book from PostgreSQL to the MongoDB according to the given ID

        # Fetch the book
        book = session.query(Book).filter(Book.rawid == rawid).first()
        # Convert to dictionary
        book_data = DataBaseHelper.book_to_dict(book)

        mongo_dict = {
            "rawid": book_data["id"],
            "title": book_data["title"],
            "author": book_data["author"],
            "year": book_data["year"],
            "price": book_data["price"],
            "genres": book_data["genres"]
        }

        # Insert to MongoDB
        books_col.insert_one(mongo_dict)

    @staticmethod
    def add_genre(new_genre_name):
        # Adds the provided genre to the PostgreSQL DB

        new_genre = session.query(Genre).filter_by(name=new_genre_name).first()
        if not new_genre:
            new_genre = Genre(name=new_genre_name)
            session.add(new_genre)
            session.commit()
            return 200, new_genre.id
        else:
            return 400, -1

    @staticmethod
    def sync_dbs():
        # Synchronize the MongoDB with PostgreSQL DB

        # Fetch MongoDB book IDs
        rawids = books_col.find({}, {
            "_id": False,
            "title": False,
            "author": False,
            "price": False,
            "year": False,
            "genres": False
        })

        # Convert to list
        mongo_list = [doc["rawid"] for doc in rawids]
        # Fetch PosgreSQL book IDs
        pgids = session.query(Book.rawid).all()
        # Convert to list
        pg_list = [row[0] for row in pgids]
        # Sort the lists
        pg_list.sort()
        mongo_list.sort()

        if pg_list != mongo_list:
            # Add the missing books to MongoDB
            for rawid in pg_list:
                if rawid not in mongo_list:
                    DataBaseHelper.add_book_to_mongo(rawid)
            # Delete irrelevant books from MongoDB
            for rawid in mongo_list:
                if rawid not in pg_list:
                    books_col.delete_one({"rawid": rawid})
