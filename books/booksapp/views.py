from django.shortcuts import render
from django.http import HttpResponse 
from django.views.decorators.http import require_http_methods
from . import models
import json
import time

@require_http_methods(["GET"])
def get_health(request):
    return HttpResponse("OK")

def book_handler(request):
    if request.method == "POST":
        return post_book(request)
    elif request.method == "GET":
        return get_book(request)
    elif request.method == "PUT":
        return update_book_price(request)
    elif request.method == "DELETE":
        return delete_book(request)
    else :
        return HttpResponse("Method not allowed", status=405)
    


def delete_book(request):
    requested_id = request.GET.get("id")
    error_message = ""
    result = ""
    if is_book_exists(requested_id):
        models.delete_book(requested_id)
        return HttpResponse(return_messege("", models.Book.objects.count()), status = 200)
    else:
        return HttpResponse(return_messege("Error: Book not found", ""), status = 404)

    


def update_book_price(request):
    requested_id = request.GET.get("id")
    requested_price = request.GET.get("price")
    code = 200
    error_message = ""
    result = ""
    if is_book_exists(requested_id):
        code, error_message = is_valid_price(requested_price)
        if code != 200:
            return HttpResponse(return_messege(error_message, ""), status = code)
        else:
            old_price = models.update_price(requested_id, requested_price)
            return HttpResponse(return_messege("", old_price), status = code)
    else:
        return HttpResponse(return_messege("Error: Book not found", ""), status = 404)

    
def post_book(request):
    result = ""
    data = json.loads(request.body)
    code, error_message = is_valid_post(data)
    if code == 200:
        new_book = models.add_book(data)
        result = new_book.rawid
    return HttpResponse(return_messege(error_message, result), status=code)


def return_messege(error_message, result):
    msg = {
                "result": result,
                "errorMessage": error_message
        }
    return json.dumps(msg)

def get_book(request):
    request_id = request.GET.get("id")
    result = ""
    error_message = ""
    code = 200
    if request_id is None:
       error_message = "Error: Missing id parameter"
       code = 400
    elif is_book_exists(request_id):
        book =  models.book_to_dict(request_id)
        result = book
        code= 200
    else:
        error_message = "Error: Book with the id [" + request_id + "] does not exist"
        code = 404
        
    return HttpResponse(return_messege(error_message, result), status=code)
     

def is_book_exists(request_id):
    return models.Book.objects.filter(rawid=request_id).exists()

def is_valid_post(data_json):
    # Checks if the post is valid
    error_message = ""
    return_code = 200
        
    cur_title = data_json["title"]
    cur_year = data_json["year"]
    price_code, error_message = is_valid_price(data_json["price"])
        
    if price_code != 200:
        return_code = price_code
    elif cur_title in [book.title for book in models.Book.objects.all()]:  # If title already in the DB
        return_code = 409
        error_message = "Error: Book with the title [" + cur_title + "] already exists in the system"
    elif cur_year < 1900 or data_json["year"] >= time.localtime().tm_year:  # If the years do not match
        return_code = 409
        error_message = "Error: Can't create new Book that its year [" + str(cur_year) + \
                                "] is not in the accepted range [1940 -> 2100]"
    elif not models.genres_match(data_json["genres"]): # If the genres do not match
        return_code = 409
        error_message = "Error: Invalid genres"
        
    return return_code, error_message

def is_valid_price(raw_price):
    # Checks if the price is valid
    return_code = 200
    error_message = ""
    try:
        num_price = int(raw_price)
        if num_price <= 0:
            return_code = 409
            error_message = "Error: Can't create new Book with negative price"
    except:
        return_code = 400
        error_message = "Error: The price should be an integer"
    return return_code, error_message

def get_books_data(request):
    # Returns the books data
    books = filter_by_params(request)
    books_data = []
    for book in books:
        books_data.append(models.book_to_dict(book.rawid))
    return HttpResponse(json.dumps(books_data), status=200)

def get_books_count(request):
    # Returns the books count
    books = filter_by_params(request)
    return HttpResponse(json.dumps({"total": books.count()}), status=200)

def filter_by_params(request):
    # Filters the books by the given parameters
    title = request.GET.get("title")
    author = request.GET.get("author")
    year = request.GET.get("year")
    price = request.GET.get("price")
    genres = request.GET.get("genres")
    books = models.Book.objects.all()
    if title:
        books = books.filter(title=title)
    if author:
        books = books.filter(author=author)
    if year:
        books = books.filter(year=year)
    if price:
        books = books.filter(price=price)
    if genres:
        genres = genres.split(",")
        books = books.filter(rawid__in=models.BookGenre.objects.filter(genre_id__in=models.Genre.objects.filter(name__in=genres)).values_list('book_rawid', flat=True))

    return books