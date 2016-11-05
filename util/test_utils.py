from utils import convert_object_to_dict


def test_convert_object_to_dict():
    class test_class:
        def __init__(self):
            self.id = 1
            self.name = "shixin"

    obj = test_class()

    d = convert_object_to_dict(obj)

    d_tppe = type(d)

    print d
    print d_tppe


if __name__ == '__main__':
    test_convert_object_to_dict()