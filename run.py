#!flask/bin/python
from app import app

if __name__ == '__main__':
    try:
        app.secret_key = 'super secret key'
        # app.run(debug=True, use_reloader=False)
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
