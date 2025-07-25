#!/usr/bin/env python3

import sys

for line in sys.stdin:
    line = line.strip()
    if line.startswith('userId'):
        continue

    fields = line.split(sep=',')
    movie_id = fields[1].strip().zfill(6)
    rating = fields[2].strip()

    print('{}\t{}'.format(movie_id, rating))