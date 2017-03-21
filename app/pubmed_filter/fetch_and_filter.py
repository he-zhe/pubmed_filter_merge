from Bio import Entrez
import xml.etree.ElementTree as ET
from .keyword_in_abstract import keyword_in_abstract
import pickle
from .ML_abstract_is_interest import ML_abstract_is_interest
import calendar
import sqlite3
import sys

# Provide email to NCBI, required
Entrez.email = "hezhe88@gmail.com"


def get_info_from_pubmed_xml(each_article):
    MedlineCitation_e = each_article.find('MedlineCitation')
    if not MedlineCitation_e:
        return

    Article_e = MedlineCitation_e.find('Article')

    # get abstract
    if Article_e.find('Abstract') is None:
        return

    if Article_e.find('Abstract').find('AbstractText') is None:
        return

    abstract_str = ''

    # Loop through AbstractText tagS, some articles divided abstract
    # into several parts.
    for abstract_tag in Article_e.iter('AbstractText'):
        if abstract_tag.text:
            abstract_str += abstract_tag.text + '\n'

    # get PMID
    PMID = MedlineCitation_e.find('PMID').text

    # get title
    try:
        title_str = Article_e.find('ArticleTitle').text
    except:
        return
    # get journal
    try:
        Journal_e = Article_e.find('Journal')
        journal_full_str = Journal_e.find('Title').text
        journal_abbr_str = Journal_e.find('ISOAbbreviation').text
    except:
        return

    # get author name list
    lastnames = []
    initials = []
    namelist = []

    for author_tag in Article_e.iter('Author'):
        if author_tag.find('LastName') is not None:
            lastnames.append(author_tag.find('LastName').text)
        else:
            lastnames.append(" ")
        if author_tag.find('Initials') is not None:
            initials.append(author_tag.find('Initials').text)
        else:
            initials.append(" ")

    for n in range(len(lastnames)):
        name = [initials[n], lastnames[n]]
        namelist.append(" ".join(name))

    namelist_str = ', '.join(namelist)

    # get publish date
    try:
        ArticleDate_e = Article_e.find('ArticleDate')
        article_year = ArticleDate_e.find('Year').text
        article_month = ArticleDate_e.find('Month').text
        article_day = ArticleDate_e.find('Day').text
    except:  # if ArticleDate not exists, use PubMedPubDate instead
        PubMedPubDate_e = each_article.find('PubmedData').find(
            'History').findall('PubMedPubDate')[0]
        article_year = PubMedPubDate_e.find('Year').text
        article_month = PubMedPubDate_e.find('Month').text
        article_day = PubMedPubDate_e.find('Day').text

    if len(article_month) > 2:
        article_month = month_dict[article_month]

    article_month = article_month.zfill(2)
    article_day = article_day.zfill(2)
    pubdate_str = article_year + '-' + article_month + '-' + \
        article_day

    return [int(PMID), title_str, journal_full_str,
            journal_abbr_str, namelist_str, abstract_str,
            pubdate_str]


def fetch_pmid_info(pmid):
    detail_handle = Entrez.efetch(db="pubmed",
                                  retstart=0,
                                  id=pmid,
                                  retmode='xml')
    detail_xml = detail_handle.read()
    tree = ET.fromstring(detail_xml)
    article = tree[0]
    return get_info_from_pubmed_xml(article)


def fetch_and_filter(RECENT_DAYS=2):

    # prepare a dict to convert 3-letter month to 2-digit
    month_dict = dict((v, k) for k, v in enumerate(calendar.month_abbr))

    # load machine learning model
    PATH = './app/pubmed_filter/model.pickle'
    with open(PATH, 'rb') as f:
        model = pickle.load(f)


    # Retrive pmids in recent X days
    search_handle = Entrez.esearch(db="pubmed", term='', reldate=RECENT_DAYS,
                                   datetype='edat', retmax='10000000')

    # Perpare a journal set for whitelist or blacklist journals
    # with open('journal_set.pickle', 'rb') as f:
    #     journal_set = pickle.load(f)

    # Retrive pmids (No detail data)
    search_records = Entrez.read(search_handle)

    # Note: This list may seem to be sorted, but exceptions may happen.
    pmid_list = search_records['IdList']

    count = int(search_records['Count'])
    print("Total # of articles: ", count)

    # articles retrived per cycle
    # https://www.ncbi.nlm.nih.gov/books/NBK25498/#chapter3.Application_3_Retrieving_large
    retmax_ = 500
    article_counter = 0

    # Connect to database that stores results
    conn = sqlite3.connect('./app/pubmed_filter/lit_rev.db')
    c = conn.cursor()

    # Main loop, retrive 500 articles, screen for interesting ones and store.
    while article_counter < count:
        print('article_counter: ', article_counter)
        pmid_500_batch = pmid_list[article_counter: article_counter + retmax_]
        http_retry_counter = 0

        while http_retry_counter < 5:
            http_retry_counter += 1
            try:
                detail_handle = Entrez.efetch(db="pubmed",
                                              retstart=0,
                                              id=','.join(pmid_500_batch),
                                              retmax=retmax_,
                                              retmode='xml')
                break
            except:
                continue
        else:
            print("Fail to retrive:{}".format(article_counter),
                  file=sys.stderr)
            continue

        article_counter += retmax_
        detail_xml = detail_handle.read()
        tree = ET.fromstring(detail_xml)
        # <PubmedArticleSet>
        #   <PubmedArticle>
        #       <MedlineCitation>
        #           <PMID>
        #           <Article>
        #               <Journal>
        #               <ArticleTitle>
        #               <Abstract>
        #               <AuthorList>
        #               <ArticleDate>
        #       <PubmedData>

        for each_article in tree:
            row = get_info_from_pubmed_xml(each_article)

            if not row:
                continue

            abstract_str = row[5]

            # Flag to track whether the article is added because of keywords
            # (KW) or machine learning(ML)
            KW_or_ML = ''

            # test if article is of interests
            if keyword_in_abstract(abstract_str):  # Deterministic
                KW_or_ML = 'KW'
            elif ML_abstract_is_interest(abstract_str, model):  # Statistic
                KW_or_ML = 'ML'
            else:
                continue
            # print(PMID)
            # print(title_str)
            # print(abstract_str)
            # print(journal_full_str)
            # print(journal_abbr_str)
            # print(namelist_str)
            # print(abstract_str)
            # print(pubdate_str)

            # stroe in database
            c.execute("""INSERT OR IGNORE INTO lit_rev (pmid, title, journal_full,
                journal_abbr, namelist, abstract, pubdate)
                VALUES(?,?,?,?,?,?,?);""", row)
            if article_counter % 10000 == 0:
                conn.commit()

    conn.commit()
    conn.close()
