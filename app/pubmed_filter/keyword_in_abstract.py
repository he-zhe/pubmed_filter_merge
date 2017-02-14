import re

# re pattern string
IR_r = r'\bir[0-9]+[a-l]\b'
GR_r = r'\bgr[0-9]+[a-l]\b'
OR_r = r'(\bor[0-9]+[a-l]\b)|(\borco\b)'
PPK_r = r'(\bppk[0-9]+[a-l]\b)'
OBP_r = r'(\bobp[0-9]+[a-l]+\b)'

re_patterns = [IR_r, GR_r, OR_r, PPK_r, OBP_r]

# keywors related to chemosensory.  Some are intentionally misspelled to
# accomadate more variations.
chemo_keywords = ['olfact', 'smell', 'chemosens', 'odor', 'odour',
                  'gustat', 'taste', 'bitter', 'sensill',
                  'chemorec', 'pheromo']


def keyword_in_abstract(abstract):
    abstract = abstract.lower()

    if 'drosophila' in abstract:
        for keyword in chemo_keywords:
            if keyword in abstract:
                # print(abstract)
                return True

    for re_pattern in re_patterns:
        if 'gene' in abstract and re.search(re_pattern, abstract):
            # print(abstract)
            return True

    return False


__all__ = [keyword_in_abstract]

if __name__ == '__main__':
    with open('pubmed_result_obp.txt', 'r') as f:
        for line in f.readlines():
            keyword_in_abstract(line)
            # print (keyword_serach(line), line)
