
class KoanError(AssertionError):
    pass


def need(condition, hint):
    if not condition:
        raise KoanError(hint)


def need_eq(actual, expected, hint):
    if actual != expected:
        raise KoanError(f"{hint}\nОжидалось: {expected}\nПолучено: {actual}")
