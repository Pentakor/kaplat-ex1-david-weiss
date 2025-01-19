from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base


DATABASE_URL = "postgresql://postgres:postgrespass@localhost:5432/books_db"
# DATABASE_URL = "postgresql://postgres:postgrespass@postgres:5432/books_db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class Book(Base):
    __tablename__ = 'book'

    rawid = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    year = Column(Integer)
    price = Column(Integer)


class BookGenre(Base):
    __tablename__ = 'book_genre'

    book_rawid = Column(Integer, ForeignKey('book.rawid'), primary_key=True)
    genre_id = Column(Integer, ForeignKey('genre.id'), primary_key=True)


class DataBasehelper:

    @staticmethod
    def book_to_dict(book):
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
    def check_genres(genres):
        for genre_name in genres:
            genre = session.query(Genre).filter_by(name=genre_name).first()
            if not genre:
                return False
        return True

    @staticmethod
    def add_book(book, genres):

        session.add(book)

        for genre_name in genres:
            genre = session.query(Genre).filter_by(name=genre_name).first()
            book_genre = BookGenre(book_rawid=book.rawid, genre_id=genre.id)
            session.add(book_genre)

        session.commit()

    @staticmethod
    def add_genre(new_genre_name):
            new_genre = session.query(Genre).filter_by(name=new_genre_name).first()
            if not new_genre:
                new_genre = Genre(name=new_genre_name)
                session.add(new_genre)
                session.commit()
                return 200, new_genre.id
            else:
                return 400, -1

