from server import *
from env_variables import *

if __name__ == "__main__":

    app.run(host=HOST, port=PORT, debug=False)
    session.close()
