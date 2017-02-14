def ML_abstract_is_interest(abstract, model):
    yhat = model.predict([abstract])
    return yhat[0]
