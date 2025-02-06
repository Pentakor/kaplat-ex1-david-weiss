# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models



class Book(models.Model):
    rawid = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    year = models.IntegerField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'book'


class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True, db_column="id")
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'genre'


class BookGenre(models.Model):  # Custom intermediate table
    id = models.AutoField(primary_key=True)
    book_rawid = models.ForeignKey(Book, on_delete=models.CASCADE, db_column="book_rawid")
    genre_id = models.ForeignKey(Genre, on_delete=models.CASCADE, db_column="genre_id")

    class Meta:
        managed = False
        db_table = 'book_genre'
        unique_together = (('book_rawid', 'genre_id'),)

    
    
def genres_match(i_genres):
    # Checks if the genres in the list are present in the PosgreSQL DB
    genres = [genre.name for genre in Genre.objects.all()]
    for item in i_genres:
        if item not in genres:
            return False
    return True

def add_book(data):
    # Adds a new book to the DB
    new_book = Book(title=data["title"], author=data["author"], year=data["year"], price=data["price"])
    new_book.save()
    for genre in data["genres"]:
        print(genre)
        new_genre = Genre.objects.get(name=genre)
        new_book_genre = BookGenre(book_rawid=new_book, genre_id=new_genre)
        new_book_genre.save()
    return new_book

def book_to_dict(requested_id):
    # Converts a book object to a dictionary
    book = Book.objects.get(rawid=requested_id)
    return {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "price": book.price,
        "genres": [genre.name for genre in Genre.objects.filter(genre_id__in=BookGenre.objects.filter(book_rawid=book.rawid).values_list('genre_id', flat=True))]
    } 

def update_price(requested_id, new_price):
    book = Book.objects.get(rawid=requested_id)
    old_price = book.price
    book.price = new_price
    book.save()
    return old_price

def delete_book(requested_id):
     book = Book.objects.get(rawid=requested_id)
     book.delete()
