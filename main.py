from flask import Flask, request
import pandas as pd
import json
import logging
from datetime import datetime
import time
import os

app = Flask(__name__)
GENRES = ["SCI_FI", "NOVEL", "HISTORY", "MANGA", "ROMANCE", "PROFESSIONAL"]
current_id = 0
df_columns = ['id', 'title', 'author', 'price', 'year', 'genres', 'lower_title', 'lower_author']
books_df = pd.DataFrame(columns=df_columns)
request_number = 0

current_directory = os.path.dirname(__file__)
new_directory_name = "logs"
new_directory_path = os.path.join(current_directory, new_directory_name)
os.makedirs(new_directory_path, exist_ok=True)


class CustomFormatter(logging.Formatter):

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = datetime.fromtimestamp(record.created).strftime('%d-%m-%Y %H:%M:%S')
        s = "%s.%03d" % (t, record.msecs)
        return s


console_handler = logging.StreamHandler()
formatter = CustomFormatter('%(asctime)s %(levelname)s : %(message)s')
console_handler.setFormatter(formatter)
logger = logging.getLogger('request-logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logs/requests.log')
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


booklogger = logging.getLogger('books-logger')
booklogger.setLevel(logging.INFO)
book_file_handler = logging.FileHandler('logs/books.log')
book_file_handler.setFormatter(formatter)
booklogger.addHandler(console_handler)
booklogger.addHandler(book_file_handler)


def log_message(message):
    return message + " | request #" + str(request_number)


def info_request(res_name, http_verb):
    return log_message('Incoming request | #'+str(request_number)+' | resource: '+res_name+' | HTTP Verb ' + http_verb)


def debug_request(duration):
    return log_message('request #'+str(request_number)+' duration: '+str(duration)+'ms')


def get_logger_level_str(my_logger):
    level = my_logger.getEffectiveLevel()
    return logging.getLevelName(level)


class Book:
    def __init__(self, my_id, title, author, year, price, genres):
        self.id = my_id
        self.title = title
        self.author = author
        self.year = year
        self.price = price
        self.genres = genres

    @staticmethod
    def json_to_book(book_json, book_id):
        book_data = book_json
        return Book(
            my_id=book_id,
            title=book_data["title"],
            author=book_data["author"],
            year=book_data["year"],
            price=book_data["price"],
            genres=book_data["genres"]
        )


class ServerHelper:

    @staticmethod
    def addbook(new_book):
        global books_df
        global current_id
        books_df.loc[len(books_df.index)] = [current_id, new_book.title, new_book.author, new_book.price, new_book.year,
                                             new_book.genres, new_book.title.lower(), new_book.author.lower()]

    @staticmethod
    def genres_match(lesser):
        global GENRES
        bigger = GENRES
        for item in lesser:
            if item not in bigger:
                return False
        return True

    @staticmethod
    def check_genres(lesser, bigger):
        for item in bigger:
            if item in lesser:
                return True
        return False

    @staticmethod
    def is_included_genre(genres, df):
        return_df = df.copy()

        for index, row in return_df.iterrows():
            if not ServerHelper.check_genres(row['genres'], genres):
                return_df = return_df.drop(return_df[return_df['id'] == row['id']].index)

        return return_df

    @staticmethod
    def is_valid_post(data_js):
        # DECLARE GLOBAL VARIABLES
        global current_id
        global books_df
        # DECLARE RETURN VALUES
        error_message = ""
        result = ""
        return_code = 200

        cur_title = data_js["title"]
        cur_year = data_js["year"]

        lower_title = cur_title.lower()
        if lower_title in books_df['lower_title'].values:
            return_code = 409
            error_message = "Error: Book with the title [" + cur_title + "] already exists in the system"
        elif cur_year < 1940 or data_js["year"] > 2100:
            return_code = 409
            error_message = "Error: Can't create new Book that its year ["+str(cur_year) + \
                            "] is not in the accepted range [1940 -> 2100]"
        elif data_js["price"] <= 0:
            return_code = 409
            error_message = "Error: Can't create new Book with negative price"
        else:
            current_id += 1
            result = current_id

        return return_code, result, error_message

    @staticmethod
    def return_message(result, error):
        msg = {
            "result": result,
            "errorMessage": error
        }
        return json.dumps(msg)

    @staticmethod
    def filter_by_params():
        f_author = request.args.get('author')
        f_price_b = request.args.get('price-bigger-than')
        f_price_l = request.args.get('price-less-than')
        f_year_b = request.args.get('year-bigger-than')
        f_year_l = request.args.get('year-less-than')
        f_genres = request.args.get('genres')

        filtered_df = books_df.copy()
        flag = 1
        if f_author is not None:
            f_author = f_author.lower()
            filtered_df = filtered_df[filtered_df['lower_author'] == f_author]
        if f_price_b is not None:
            filtered_df = filtered_df[filtered_df['price'] >= int(f_price_b)]
        if f_price_l is not None:
            filtered_df = filtered_df[filtered_df['price'] <= int(f_price_l)]
        if f_year_b is not None:
            filtered_df = filtered_df[filtered_df['year'] >= int(f_year_b)]
        if f_year_l is not None:
            filtered_df = filtered_df[filtered_df['year'] <= int(f_year_l)]
        if f_genres is not None:
            f_genres = f_genres.split(",")
            flag = ServerHelper.genres_match(f_genres)
            filtered_df = ServerHelper.is_included_genre(f_genres, filtered_df)

        return filtered_df, flag


class Server:

    @staticmethod
    @app.route('/books/health', methods=['GET'])
    def get_books_health():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/books/health', 'GET'))
        logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
        return "OK", 200

    @staticmethod
    @app.route('/book', methods=['POST'])
    def post_book():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/book', 'POST'))
        global books_df

        # GET DATA FROM POST REQUEST
        raw_book = request.get_json()
        # CHECK IF EVERYTHING IS OK
        return_code, result, error_message = ServerHelper.is_valid_post(raw_book)
        if return_code == 200:
            new_book = Book.json_to_book(raw_book, current_id)
            dict_title = new_book.title

            booklogger.info(log_message("Creating new Book with Title [{0}]".format(dict_title)))
            booklogger.debug(log_message(
                "Currently there are {0} Books in the system. New Book will be assigned with id {1}".format(
                    len(books_df), current_id)))

            ServerHelper.addbook(new_book)
        else:
            booklogger.error(log_message(error_message))

        logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
        return ServerHelper.return_message(result, error_message), return_code

    @staticmethod
    @app.route('/books/total', methods=['GET'])
    def get_books_count():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/books/total', 'GET'))
        filtered_df, flag = ServerHelper.filter_by_params()
        count_row = filtered_df.shape[0]
        result = 0
        if flag:
            result = 200
            booklogger.info(log_message("Total Books found for requested filters is {0}".format(count_row)))
        else:
            result = 400
        logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
        return ServerHelper.return_message(count_row, ""), result

    @staticmethod
    @app.route('/books', methods=['GET'])
    def get_books_data():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/books', 'GET'))
        filtered_df, flag = ServerHelper.filter_by_params()
        filtered_df = filtered_df.sort_values(by='lower_title')
        filtered_df = filtered_df.drop(columns=['lower_title', 'lower_author'])
        json_array = filtered_df.to_json(orient='records')
        count_row = filtered_df.shape[0]
        result = 0
        if flag:
            result = 200
            booklogger.info(log_message("Total Books found for requested filters is {0}".format(count_row)))
        else:
            result = 400
        logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
        return ServerHelper.return_message(json_array, ""), result

    @staticmethod
    @app.route('/book', methods=['GET'])
    def get_book_data():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/book', 'GET'))
        global books_df
        requested_id = request.args.get('id')
        return_df = books_df[books_df['id'] == int(requested_id)]
        return_df = return_df.drop(columns=['lower_title', 'lower_author'])
        try:
            row = return_df.iloc[0].to_dict()
            json_data = json.dumps(row, indent=4)
            print(json_data)
            booklogger.debug(log_message("Fetching book id {0} details".format(requested_id)))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message(json_data, ""), 200
        except:
            booklogger.error(log_message("Error: no such Book with id " + requested_id))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404

    @staticmethod
    @app.route('/book', methods=['PUT'])
    def update_price():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/book', 'PUT'))
        global books_df
        requested_id = int(request.args.get('id'))
        new_price = int(request.args.get('price'))
        if new_price <= 0:
            booklogger.error(log_message("Error: price update for book [" + str(
                requested_id) + "] must be a positive integer"))
            logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
            return ServerHelper.return_message("", "Error: price update for book [" + str(
                requested_id) + "] must be a positive integer"), 409
        return_df = books_df[books_df['id'] == int(requested_id)]
        try:
            row = return_df.iloc[0].to_dict()
            old_price = row['price']
            books_df.loc[books_df['id'] == requested_id, 'price'] = new_price
            booklogger.info(log_message("Update Book id [{0}] price to {1}".format(requested_id, new_price)))
            booklogger.debug(log_message("Book [{0}] price change: {1} --> {2}".format(requested_id, old_price, new_price)))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message(old_price, ""), 200
        except:
            booklogger.error(log_message("Error: no such Book with id " + str(requested_id)))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message("", "Error: no such Book with id " + str(requested_id)), 404

    @staticmethod
    @app.route('/book', methods=['DELETE'])
    def delete_book():
        start_time = time.perf_counter() * 1000
        global request_number
        request_number += 1
        logger.info(info_request('/book', 'DELETE'))
        global books_df
        requested_id = request.args.get('id')
        return_df = books_df[books_df['id'] == int(requested_id)]
        title_value = return_df.loc[return_df['id'] == int(requested_id), 'title'].values[0]
        return_df = return_df.drop(columns=['lower_title', 'lower_author'])
        try:
            row = return_df.iloc[0].to_dict()
            books_df = books_df.drop(books_df[books_df['id'] == int(requested_id)].index)
            num_rows = books_df.shape[0]
            booklogger.info(log_message("Removing book [{0}]".format(title_value)))
            booklogger.debug(log_message(
                "After removing book [{0}] id: [{1}] there are {2} books in the system"
                .format(title_value, requested_id, len(books_df))))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message(str(num_rows), ""), 200
        except:
            booklogger.error(log_message("Error: no such Book with id " + requested_id))
            logger.debug(debug_request(round(time.perf_counter()*1000 - start_time)))
            return ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404

    @staticmethod
    @app.route('/logs/level', methods=['PUT'])
    def set_logger_level():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/logs/level', 'PUT'))
        requested_logger = request.args.get('logger-name')
        requested_logger_level = request.args.get('logger-level')
        print(requested_logger)
        print(requested_logger_level)
        try:
            if requested_logger == 'request-logger':
                logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
                logger.setLevel(requested_logger_level)
                return get_logger_level_str(logger), 200
            elif requested_logger == 'books-logger':
                logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
                booklogger.setLevel(requested_logger_level)
                return get_logger_level_str(booklogger), 200
            else:
                logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
                return "No such logger in the system", 404
        except:
            logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
            return "No such logger level", 404

    @staticmethod
    @app.route('/logs/level', methods=['GET'])
    def get_logger_level():
        global request_number
        request_number += 1
        start_time = time.perf_counter() * 1000
        logger.info(info_request('/logs/level', 'GET'))
        requested_logger = request.args.get('logger-name')
        if requested_logger == 'request-logger':
            logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
            return get_logger_level_str(logger), 200
        elif requested_logger == 'books-logger':
            logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
            return get_logger_level_str(booklogger), 200
        else:
            logger.debug(debug_request(round(time.perf_counter() * 1000 - start_time)))
            return "No such logger in the system", 404


if __name__ == "__main__":
    app.run(host='localhost', port=8574, debug=True)
