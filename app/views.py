from app import app
import sqlite3
from app.rows_by_dates import rows_in_month
from flask import render_template, flash, request, url_for, redirect, make_response
from datetime import date
import json
from wtforms import Form, StringField, validators
from app.pubmed_filter.fetch_and_filter import fetch_pmid_info

conn = sqlite3.connect('./app/pubmed_filter/lit_rev.db',
                       check_same_thread=False)
c = conn.cursor()

conn_training = sqlite3.connect('./app/pubmed_filter/training_set.db',
                       check_same_thread=False)
c_training = conn_training.cursor()


recent_12_months = []
year_walk = current_year = date.today().year
month_walk = current_month = date.today().month
recent_12_months.append((current_year, current_month))

for i in range(11):
    month_walk -= 1
    if month_walk > 0:
        recent_12_months.append((year_walk, month_walk))
    else:
        month_walk = 12
        year_walk -= 1
        recent_12_months.append((year_walk, month_walk))


@app.route('/')
@app.route('/index')
@app.route('/<int:year>/<int:month>')
def entry(year=date.today().year, month=date.today().month):
    cookie_name = 'history' + str(year) + str(month).zfill(2)

    # Get read history
    history_str = request.cookies.get(cookie_name)
    if history_str:
        history_set = set(json.loads(history_str))
    else:
        history_set = set()

    #  Get all entries for the month from db
    entries = list(rows_in_month(c, month, year))

    #  Find all unread entries
    new_set = set()
    for e in entries:
        if e[0] not in history_set:
            new_set.add(e[0])

    res = make_response(render_template("entry.html",
                        recent_12_months=recent_12_months,
                        rows=entries,
                        new_set=new_set,
                        title=str(month) + '/' + str(year)))

    #  Update history set
    for e in entries:
        history_set.add(e[0])

    #  Why save history for each month, instead of all in one?
    #  It will exceed maximun size requiement of a single cookie.
    #  http://browsercookielimits.squawky.net/
    #  Note: This might fail due to a large amount of enties for a month.
    #  > ~400
    res.set_cookie(cookie_name, json.dumps(list(history_set)),
                   max_age=2147483647)
    return res


@app.route('/submit_neg/<int:pmid>')
def submit_neg(pmid):
    if not isinstance(pmid, int):
        return
    with open('./app/static/neg_submit.txt', 'a') as f:
        f.write(str(pmid) + '\n')
    return str(pmid) + " has been added to negative training set. Thank you!"


class PMID_form(Form):
    pmid = StringField('pmid', [validators.Length(min=1, max=9)])


@app.route('/submit_pos', methods=['GET', 'POST'])
def submit_pos():
    form = PMID_form(request.form)
    if request.method == 'POST' and form.validate():
        pmid = form.pmid.data
        if not (pmid.isdigit() and len(pmid) < 10):
            flash('Not a correct format of PMID')
            return redirect(url_for('submit_pos'))
        with open('./app/static/pos_submit.txt', 'a') as f:
            f.write(str(pmid) + '\n')
        flash('Thanks for submitting paper!')
        return redirect(url_for('submit_pos'))
    return render_template('submit_pos.html', form=form,
                           recent_12_months=recent_12_months,
                           title='Suggest Papers')


# Manage neg page
@app.route('/bitter', methods=['GET', 'POST'])
@app.route('/sweet', methods=['GET', 'POST'])
def manage():
    rule = request.url_rule

    if 'bitter' in rule.rule:
        pos_or_neg = 'neg'
        title = 'Submitted Negative entries'
        path = './app/static/neg_submit.txt'
    elif 'sweet' in rule.rule:
        pos_or_neg = 'pos'
        title = 'Submitted Positive entries'
        path = './app/static/pos_submit.txt'

    if request.method == 'GET':
        with open(path, 'r') as f:
            pmids = set(f.readlines())
            if pos_or_neg == 'neg':
                rows = c.execute('SELECT * FROM lit_rev WHERE pmid in ({0})'.format(','.join(pmids)))
            else:
                rows = []
                for pmid in pmids:
                    c.execute('SELECT * FROM lit_rev WHERE pmid=?', (pmid,))
                    if len(c.fetchall()) > 0:
                        continue
                    rows.append(fetch_pmid_info(pmid))
        return render_template("manage.html",
                               recent_12_months=recent_12_months,
                               rows=rows,
                               title=title)
    elif request.method == 'POST':
        pmids = request.form.getlist('check')
        for pmid in pmids:
            if pos_or_neg == 'neg':
                c.execute('SELECT * FROM lit_rev WHERE pmid=?', (pmid,))
                row = c.fetchone()
            else:
                row = fetch_pmid_info(pmid)

            abstract = row[5]
            c_training.execute("INSERT INTO training_set VALUES(?, ?);", (abstract, pos_or_neg))
            if pos_or_neg == 'neg':
                c.execute('DELETE FROM lit_rev WHERE pmid=?', (pmid,))
            else:
                c.execute("""INSERT OR IGNORE INTO lit_rev (pmid, title, journal_full,
                    journal_abbr, namelist, abstract, pubdate)
                    VALUES(?,?,?,?,?,?,?);""", row)
        conn_training.commit()
        conn.commit()
        return ','.join(pmids) + ' has been processed in lit_rev and stored in training_set: ' + pos_or_neg


@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')
