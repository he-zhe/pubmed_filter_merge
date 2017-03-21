#!flask/bin/python
from app import app
app.secret_key = 'super secret key'

with open('secret_key.txt', 'r') as f:
    app.secret_key = f.read().strip()

if __name__ == '__main__':
    try:
        # app.run(debug=True, use_reloader=False)
        app.run()
    except (KeyboardInterrupt, SystemExit):
        pass
