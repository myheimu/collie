

def encode(value):
    value = value.replace(" ", "%20")
    return value


def decode(value):
    value = value.replace("%20", " ")
    return value
