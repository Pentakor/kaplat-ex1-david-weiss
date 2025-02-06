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


class BookGenre(models.Model):
    book_rawid = models.OneToOneField(Book, models.DO_NOTHING, db_column='book_rawid', primary_key=True)  # The composite primary key (book_rawid, genre_id) found, that is not supported. The first column is selected.
    genre = models.ForeignKey('Genre', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'book_genre'
        unique_together = (('book_rawid', 'genre'),)


class Genre(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'genre'
