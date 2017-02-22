#!flask/bin/python
from app import app
app.secret_key = 'tf0YYZSq8wTDyNRoI3fwo7ey344Gw6Ay'

if __name__ == '__main__':
    try:
        # app.run(debug=True, use_reloader=False)
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
