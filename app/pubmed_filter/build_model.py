import time
import pickle

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report as clsr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split as tts

from random import randint


def timeit(func):
    """
    Simple timing decorator
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        delta = time.time() - start
        return result, delta
    return wrapper


def identity(arg):
    """
    Simple identity function works as a passthrough.
    """
    return arg


@timeit
def build_and_evaluate(X, y, classifier=SGDClassifier, outpath=None,
                       verbose=True):

    @timeit
    def build(classifier, X, y=None):
        """
        Inner build function that builds a single model.
        """

        model = Pipeline([
            ('vectorizer', TfidfVectorizer()),
            ('classifier', classifier()),
        ])

        model.fit(X, y)
        return model

    # Label encode the targets
    labels = LabelEncoder()
    y = labels.fit_transform(y)

    # Begin evaluation
    if verbose:
        print("Building for evaluation")
    X_train, X_test, y_train, y_test = tts(X, y, test_size=0.2)
    model, secs = build(classifier, X_train, y_train)

    if verbose:
        print("Evaluation model fit in {:0.3f} seconds".format(secs))
    if verbose:
        print("Classification Report:\n")

    y_pred = model.predict(X_test)
    print(clsr(y_test, y_pred, target_names=labels.classes_))

    if verbose:
        print("Building complete model and saving ...")
    model, secs = build(classifier, X, y)
    model.labels_ = labels

    if verbose:
        print("Complete model fit in {:0.3f} seconds".format(secs))

    if outpath:
        with open(outpath, 'wb') as f:
            pickle.dump(model, f)

        print("Model written out to {}".format(outpath))

    return model


def build_model():
    PATH = "./app/pubmed_filter/model.pickle"

    import sqlite3
    conn = sqlite3.connect('./app/pubmed_filter/training_set.db')
    c = conn.cursor()
    all_rows = c.execute('select * from training_set')

    X = []
    y = []

    for row in all_rows:
        if row[1] == 'pos':  # Overrepresent pos cases
            n = randint(0, 4)
            while n > 0:
                X.append(row[0])
                y.append(row[1])
                n -= 1
        X.append(row[0])
        y.append(row[1])

    conn.close()
    model, secs = build_and_evaluate(X, y, outpath=PATH)


if __name__ == "__main__":
    build_model()
