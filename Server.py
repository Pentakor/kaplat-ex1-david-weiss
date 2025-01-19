from flask import Flask, request
import json
from DatabaseConnections import *
from logManager import *

app = Flask(__name__)
request_number = 0
logs = LogManager()


class Server:

    class ServerHelper:
      
        @staticmethod
        def does_book_exist(book_id):
            try:
                num_id = int(book_id)  # Attempt to convert to integer
                exists = session.query(Book).filter(Book.rawid == num_id).count() > 0
            except ValueError:
                exists = False  # If conversion fails, `exists` remains False

            return exists

        @staticmethod
        def json_to_book(book_json):
            return Book(
                title=book_json["title"],  # Extract title from JSON
                author=book_json["author"],  # Extract author from JSON
                year=book_json["year"],  # Extract year from JSON
                price=book_json["price"],  # Extract price from JSON
            )

        @staticmethod
        def genres_match(lesser):
            genres = [genre.name for genre in session.query(Genre.name).all()]
            for item in lesser:
                if item not in genres:
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
                if not Server.ServerHelper.check_genres(row['genres'], genres):
                    return_df = return_df.drop(return_df[return_df['id'] == row['id']].index)

            return return_df

        @staticmethod
        def is_valid_price(raw_price):
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

        @staticmethod
        def is_valid_post(data_json):
            # DECLARE RETURN VALUES
            error_message = ""
            return_code = 200

            cur_title = data_json["title"]
            cur_year = data_json["year"]
            price_code, error_message = Server.ServerHelper.is_valid_price(data_json["price"])

            if price_code != 200:
                return_code = price_code
            elif cur_title in [book.title for book in session.query(Book.title).all()]:
                return_code = 409
                error_message = "Error: Book with the title [" + cur_title + "] already exists in the system"
            elif cur_year < 1940 or data_json["year"] > 2100:
                return_code = 409
                error_message = "Error: Can't create new Book that its year [" + str(cur_year) + \
                                "] is not in the accepted range [1940 -> 2100]"
            elif not DataBasehelper.check_genres(data_json["genres"]):
                return_code = 409
                error_message = "Error: Invalid genres"

            return return_code, error_message

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

            query = session.query(Book)
            flag = 1
            if f_author is not None:
                query = query.filter(Book.author == f_author)

            if f_price_b is not None:
                query = query.filter(Book.price >= int(f_price_b))

            if f_price_l is not None:
                query = query.filter(Book.price <= int(f_price_l))

            if f_year_b is not None:
                query = query.filter(Book.year >= int(f_year_b))

            if f_year_l is not None:
                query = query.filter(Book.year <= int(f_year_l))

            if f_genres is not None:
                genres = f_genres.split(',')
                query = query.join(BookGenre).join(Genre).filter(Genre.name.in_(genres))
                flag = Server.ServerHelper.genres_match(genres)
            return query.all(), flag

    @staticmethod
    @app.route('/books/health', methods=['GET'])
    def get_books_health():
        global request_number
        global logs
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/books/health', 'GET', request_number))
        logs.get_requests().debug(logs.debug_request(start_time, request_number))
        books = session.query(Book).all()
        return "OK", 200

    @staticmethod
    @app.route('/book', methods=['POST'])
    def post_book():
        global request_number
        request_number += 1
        result = ""
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/book', 'POST', request_number))

        # GET DATA FROM POST REQUEST
        raw_book = request.get_json()
        # CHECK IF EVERYTHING IS OK
        return_code, error_message = Server.ServerHelper.is_valid_post(raw_book)
        if return_code == 200:

            new_book = Server.ServerHelper.json_to_book(raw_book)
            dict_title = new_book.title

            logs.get_books().info(logs.message("Creating new Book with Title [{0}]".format(dict_title), request_number))
            logs.get_books().debug(logs.message(
                "Currently there are {0} Books in the system. New Book will be assigned with id {1}".format(
                    session.query(Book).count(), new_book.rawid), request_number))

            DataBasehelper.add_book(new_book, raw_book["genres"])
            result = new_book.rawid
        else:
            logs.get_books().error(logs.message(error_message, request_number))

        logs.get_requests().debug(logs.debug_request(start_time, request_number))
        return Server.ServerHelper.return_message(result, error_message), return_code

    @staticmethod
    @app.route('/books/total', methods=['GET'])
    def get_books_count():
        global request_number
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/books/total', 'GET', request_number))
        filtered_books_list, flag = Server.ServerHelper.filter_by_params()
        count_row = len(filtered_books_list)
        result = 0
        if flag:
            result = 200
            logs.get_books().info(logs.message(
                "Total Books found for requested filters is {0}".format(count_row), request_number))
        else:
            result = 400
        logs.get_requests().debug(logs.debug_request(start_time, request_number))
        return Server.ServerHelper.return_message(count_row, ""), result

    @staticmethod
    @app.route('/books', methods=['GET'])
    def get_books_data():
        global request_number
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/books', 'GET', request_number))
        filtered_books_list, flag = Server.ServerHelper.filter_by_params()
        serialized_list = [DataBasehelper.book_to_dict(book) for book in filtered_books_list]
        result = 0
        if flag:
            result = 200
            logs.get_books().info(logs.message(
                "Total Books found for requested filters is {0}".format(len(filtered_books_list)), request_number))
        else:
            result = 400
        logs.get_requests().debug(logs.debug_request(start_time, request_number))
        return Server.ServerHelper.return_message(serialized_list, ""), result

    @staticmethod
    @app.route('/book', methods=['GET'])
    def get_book_data():
        global request_number
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/book', 'GET', request_number))
        requested_id = request.args.get('id')
        try:
            if Server.ServerHelper.does_book_exist(requested_id):

                book = session.query(Book).filter(Book.rawid == requested_id).first()
                book_data = DataBasehelper.book_to_dict(book)
                logs.get_books().debug(logs.message("Fetching book id {0} details".format(requested_id),  request_number))
                logs.get_requests().debug(logs.debug_request(start_time, request_number))
                return Server.ServerHelper.return_message(book_data, ""), 200
            else:
                raise Exception()
        except:
            logs.get_books().error(logs.message("Error: no such Book with id " + requested_id, request_number))
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return Server.ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404

    @staticmethod
    @app.route('/book', methods=['PUT'])
    def update_price():
        global request_number
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/book', 'PUT', request_number))
        requested_id = request.args.get('id')
        price_code, error_message = Server.ServerHelper.is_valid_price(request.args.get('price'))

        if price_code != 200:
            logs.get_books().error(logs.message("Error: price update for book [" + str(
                requested_id) + "] must be a positive integer", request_number))
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return Server.ServerHelper.return_message("", "Error: price update for book [" + str(
                requested_id) + "] must be a positive integer"), 409
        else:
            new_price = int(request.args.get('price'))

        try:
            if Server.ServerHelper.does_book_exist(requested_id):
                book = session.query(Book).filter(Book.rawid == requested_id).first()
                old_price = book.price
                book.price = new_price
                session.commit()
                logs.get_books().debug(logs.message(
                    "Book [{0}] price change: {1} --> {2}".format(requested_id, old_price, new_price), request_number))
                logs.get_requests().debug(logs.debug_request(start_time, request_number))
                return Server.ServerHelper.return_message(old_price, ""), 200
            else:
                raise Exception()
        except:
            logs.get_books().error(logs.message("Error: no such Book with id " + str(requested_id), request_number))
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return Server.ServerHelper.return_message("", "Error: no such Book with id " + str(requested_id)), 404

    @staticmethod
    @app.route('/book', methods=['DELETE'])
    def delete_book():
        start_time = time.perf_counter() 
        global request_number
        request_number += 1
        logs.get_requests().info(logs.info_request('/book', 'DELETE', request_number))
        requested_id = request.args.get('id')
        try:
            if Server.ServerHelper.does_book_exist(requested_id):
                book = session.query(Book).filter(Book.rawid == requested_id).first()
                book_data = DataBasehelper.book_to_dict(book)
                session.query(BookGenre).filter(BookGenre.book_rawid == requested_id).delete(synchronize_session =
                                                                                             'fetch')
                session.delete(book)
                session.commit()
                logs.get_books().info(logs.message("Removing book [{0}]".format(book_data["title"]),  request_number))
                logs.get_books().debug(logs.message(
                    "After removing book [{0}] id: [{1}] there are {2} books in the system"
                    .format(book_data["title"], requested_id, session.query(Book).count()), request_number))
                logs.get_requests().debug(logs.debug_request(start_time,  request_number))
                return Server.ServerHelper.return_message(session.query(Book).count(), ""), 200
            else:
                raise Exception()
        except:
            logs.get_books().error(logs.message("Error: no such Book with id " + requested_id, request_number))
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return Server.ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404

    @staticmethod
    @app.route('/logs/level', methods=['PUT'])
    def set_logger_level():
        print("A")
        global request_number
        request_number += 1
        start_time = time.perf_counter()
        logs.get_requests().info(logs.info_request('/logs/level', 'PUT', request_number))
        requested_logger = request.args.get('logger-name')
        requested_logger_level = request.args.get('logger-level')
        print(requested_logger)
        print(requested_logger_level)
        try:
            if requested_logger == 'request-logger':
                logs.get_requests().debug(logs.debug_request(start_time, request_number))
                logs.get_requests().setLevel(requested_logger_level)
                return logs.get_requests_level_str(logs.get_requests()), 200
            elif requested_logger == 'books-logger':
                logs.get_requests().debug(logs.debug_request(start_time,  request_number))
                logs.get_books().setLevel(requested_logger_level)
                return logs.get_requests_level_str(logs.get_books()), 200
            else:
                logs.get_requests().debug(logs.debug_request(start_time, request_number))
                return "No such log in the system", 404
        except:
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return "No such log level", 404

    @staticmethod
    @app.route('/logs/level', methods=['GET'])
    def get_requests_level():
        global request_number
        request_number += 1
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/logs/level', 'GET', request_number))
        requested_logger = request.args.get('logger-name')
        if requested_logger == 'request-logger':
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return logs.get_requests_level_str(logs.get_requests()), 200
        elif requested_logger == 'books-logger':
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return logs.get_requests_level_str(logs.get_books()), 200
        else:
            logs.get_requests().debug(logs.debug_request(start_time, request_number))
            return "No suchlogs.get_requests() in the system", 404

    @staticmethod
    @app.route('/genre', methods=['POST'])
    def post_genre():
        global request_number
        request_number += 1
        result = ""
        error_message = ""
        start_time = time.perf_counter() 
        logs.get_requests().info(logs.info_request('/book', 'POST', request_number))
        genre_json = request.get_json()
        genre_name = genre_json["genre"]
        return_code, genre_id = DataBasehelper.add_genre(genre_name)
        if return_code == 200:

            logs.get_books().info(logs.message("Adding new genre: [{0}]".format(genre_name), request_number))
            logs.get_books().debug(logs.message(
                "Currently there are {0} Genres in the system. New Genre will be assigned with id {1}".format(
                    session.query(Genre).count() - 1, genre_id), request_number))
            result = genre_id

        else:
            error_message = "Error: Genre already exists in the system."
            logs.get_books().error(logs.message(error_message, request_number))

        logs.get_requests().debug(logs.debug_request(start_time, request_number))
        return Server.ServerHelper.return_message(result, error_message), return_code
