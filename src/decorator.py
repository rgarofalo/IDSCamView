def disabled(func):
    def inner(*args, **kwargs):
        pass

    return inner
