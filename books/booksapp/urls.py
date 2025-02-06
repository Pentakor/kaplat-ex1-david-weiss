from django.urls import path

from . import views

urlpatterns = [
    path("book", views.book_handler, name="book"),
    path("books/health", views.get_health, name="health"),
    path("books/total", views.get_books_count, name="books"),
    path("books", views.get_books_data, name="books")
]