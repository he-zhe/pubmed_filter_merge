from app import app
import sqlite3
from app.rows_by_dates import rows_in_month
from flask import render_template, flash, request, url_for, redirect
from datetime import date
# from flask_wtf import FlaskForm
from wtforms import Form, StringField, validators

with open("./app/static/journal.txt", 'r') as f:
    journal_rank = {line.strip().lower(): i for i, line in enumerate(f)}

conn = sqlite3.connect('./app/pubmed_filter/lit_rev.db',
                       check_same_thread=False)
c = conn.cursor()


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
    entries = list(rows_in_month(c, month, year))

    # sort rows by pre-defined journal rank, if not existed, put to last
    entries.sort(key=lambda x: journal_rank[x[2].lower()] if x[2].lower() in journal_rank else 999)
    return render_template("entry.html",
                           recent_12_months=recent_12_months,
                           rows=entries,
                           title=str(month) + '/' + str(year))


@app.route('/submit_neg/<int:pmid>')
def submit_neg(pmid):
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


@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')
