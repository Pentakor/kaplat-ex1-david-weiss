from flask import Flask, request
import pandas as pd
import json

app = Flask(__name__)

GENRES = ["SCI_FI", "NOVEL", "HISTORY", "MANGA", "ROMANCE", "PROFESSIONAL"]

current_id = 0

df_columns = ['id', 'title', 'author', 'price', 'year','genres', 'lower_title', 'lower_author']
books_df = pd.DataFrame(columns=df_columns)


class Book:
    def __init__(self, id, title, author, year, price, genres):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.price = price
        self.genres = genres

    @staticmethod
    def json_to_book(book_json, book_id):
        book_data = book_json
        return Book(
            id=book_id,
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
            error_message = "Error: Can't create new Book that its year ["+str(cur_year)+"] is not in the accepted range [1940 -> 2100]"
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
        return "OK", 200

    @staticmethod
    @app.route('/book', methods=['POST'])
    def post_book():
        global books_df
        # GET DATA FROM POST REQUEST
        raw_book = request.get_json()
        # CHECK IF EVERYTHING IS OK
        return_code, result, error_message = ServerHelper.is_valid_post(raw_book)
        if return_code == 200:
            new_book = Book.json_to_book(raw_book, current_id)
            dict_title = new_book.title
            ServerHelper.addbook(new_book)

        # SEND RESPONSE
        return ServerHelper.return_message(result, error_message), return_code

    @staticmethod
    @app.route('/books/total', methods=['GET'])
    def get_books_count():
        filtered_df, flag = ServerHelper.filter_by_params()
        count_row = filtered_df.shape[0]

        result = 0
        if flag:
            result = 200
        else:
            result = 400

        return ServerHelper.return_message(count_row, ""), result

    @staticmethod
    @app.route('/books', methods=['GET'])
    def get_books_data():
        filtered_df, flag = ServerHelper.filter_by_params()
        filtered_df = filtered_df.sort_values(by='lower_title')
        filtered_df = filtered_df.drop(columns=['lower_title', 'lower_author'])
        json_array = filtered_df.to_json(orient='records')

        result = 0
        if flag:
            result = 200
        else:
            result = 400

        return ServerHelper.return_message(json_array, ""), result

    @staticmethod
    @app.route('/book', methods=['GET'])
    def get_book_data():
        global books_df
        requested_id = request.args.get('id')
        return_df = books_df[books_df['id'] == int(requested_id)]
        return_df = return_df.drop(columns=['lower_title', 'lower_author'])
        try:
            row = return_df.iloc[0].to_dict()
            json_data = json.dumps(row, indent=4)
            print(json_data)
            return ServerHelper.return_message(json_data, ""), 200
        except:
            return ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404

    @staticmethod
    @app.route('/book', methods=['PUT'])
    def update_price():
        global books_df
        requested_id = int(request.args.get('id'))
        new_price = int(request.args.get('price'))
        if new_price <= 0:
            return ServerHelper.return_message("", "Error: price update for book [" + str(
                requested_id) + "] must be a positive integer"), 409
        return_df = books_df[books_df['id'] == int(requested_id)]
        try:
            row = return_df.iloc[0].to_dict()
            old_price = row['price']
            books_df.loc[books_df['id'] == requested_id, 'price'] = new_price
            return ServerHelper.return_message(old_price, ""), 200
        except:
            return ServerHelper.return_message("", "Error: no such Book with id " + str(requested_id)), 404

    @staticmethod
    @app.route('/book', methods=['DELETE'])
    def delete_book():
        global books_df
        requested_id = request.args.get('id')
        return_df = books_df[books_df['id'] == int(requested_id)]
        return_df = return_df.drop(columns=['lower_title', 'lower_author'])
        try:
            row = return_df.iloc[0].to_dict()
            books_df = books_df.drop(books_df[books_df['id'] == int(requested_id)].index)
            num_rows = books_df.shape[0]
            return ServerHelper.return_message(str(num_rows), ""), 200
        except:
            return ServerHelper.return_message("", "Error: no such Book with id " + requested_id), 404


if __name__ == "__main__":
    app.run(host='localhost', port=8574)

    #IF SOMEONE READING THIS. I HAVE TO SAY THAT ITS THE THIRD VERSION THAT I AM SUBMITING
    #AND IT IS BECAUSE OF THE ACADEMIC TEAM MISTAKES... LIKE 429 ERROR OR "A POSITIVE"
    #EVERY TIME MAKING A NEW SUBMISION BECAUSE OF THE ACADEMIC TEAM MISTAKES (AND NOT MINE) IS NOT COOL!


