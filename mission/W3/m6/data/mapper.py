#!/usr/bin/env python3

import sys

for line in sys.stdin:
    line = line.strip()
    if line.startswith('user_Id'):
        continue

    fields = line.split(sep=',')
    product_id = fields[1].strip()
    rating = fields[2].strip()

    print('{}\t{}'.format(product_id, rating))