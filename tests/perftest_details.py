from subprocess import call
from timeit import timeit, repeat

# for most consistent results check that SQLALCHEMY_ECHO disabled,
# stdout echo disabled on profiler if profiling is enabled and
# debug is disabled.

def download_details(textId):
    call(["/usr/bin/wget", "-q", "-O", "/dev/null", "http://127.0.0.1:25000/iiab/books/text/%s/details" % textId])

def do_test(textId):
    print("testing " + textId)
    results = repeat("download_details('{0}')".format(textId), 'from __main__ import download_details', repeat=20, number=1)
    print(results)
    print("mean={0}".format(sum(results)/len(results)))

print("skipping first test because has overhead")
download_details('etext1111')

do_test('etext31547')
do_test('etext31177')

