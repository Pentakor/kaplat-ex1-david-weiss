import logging
import time
from datetime import datetime
import os


class LogManager:

    class CustomFormatter(logging.Formatter):

        def formatTime(self, record, datefmt=None):
            ct = self.converter(record.created)
            t = datetime.fromtimestamp(record.created).strftime('%d-%m-%Y %H:%M:%S')
            s = "%s.%03d" % (t, record.msecs)
            return s

    def __init__(self):
        current_directory = os.path.dirname(__file__)
        new_directory_name = "logs"
        new_directory_path = os.path.join(current_directory, new_directory_name)
        os.makedirs(new_directory_path, exist_ok=True)

        console_handler = logging.StreamHandler()
        formatter = self.CustomFormatter('%(asctime)s %(levelname)s : %(message)s')
        console_handler.setFormatter(formatter)
        file_handler = logging.FileHandler('logs/requests.log')
        file_handler.setFormatter(formatter)
        book_file_handler = logging.FileHandler('logs/books.log')
        book_file_handler.setFormatter(formatter)

        self.requests = logging.getLogger('request-logger')
        self.requests.setLevel(logging.INFO)

        self.requests.addHandler(console_handler)
        self.requests.addHandler(file_handler)

        self.books = logging.getLogger('books-logger')
        self.books.setLevel(logging.INFO)

        self.books.addHandler(console_handler)
        self.books.addHandler(book_file_handler)

    def get_requests(self):
        return self.requests

    def get_books(self):
        return self.books

    @staticmethod
    def calc_duration(start_time):
        return round(time.perf_counter() * 1000 - start_time * 1000)

    @staticmethod
    def message(message, request_number):
        return message + " | request #" + str(request_number)

    @staticmethod
    def info_request(res_name, http_verb, request_number):
        return LogManager.message(
            ' resource: ' + res_name + ' | HTTP Verb '
            + http_verb, request_number)

    @staticmethod
    def debug_request(start_time, request_number):
        return LogManager.message('request #' + str(request_number) + ' duration: '
                                      + str(LogManager.calc_duration(start_time))
                                      + 'ms', request_number)

    @staticmethod
    def get_requests_level_str(my_logger):
        level = my_logger.getEffectiveLevel()
        return logging.getLevelName(level)


