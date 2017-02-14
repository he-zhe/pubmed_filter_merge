#!flask/bin/python
from app import app
app.secret_key = 'super super secret key'

if __name__ == '__main__':
    try:
        # app.run(debug=True, use_reloader=False)
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
