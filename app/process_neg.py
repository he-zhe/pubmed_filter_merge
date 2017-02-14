# This script will remove entries marked as neg
# and record those in neg training set.
import sqlite3

with open("./app/static/neg_submit.txt", 'r') as f:
    neg_set = set(f.readlines())

conn = sqlite3.connect('./app/static/lit_rev.db')
c = conn.cursor()

for pmid in neg_set:
    c.execute('DELETE FROM lit_rev WHERE pmid=?', (pmid,))

conn.commit()
conn.close()
