import collections


def tree():
    return collections.defaultdict(tree)

if __name__ == "__main__":
    print "hello world"