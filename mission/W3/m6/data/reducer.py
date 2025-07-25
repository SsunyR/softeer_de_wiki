#!/usr/bin/env python3

import sys

current_product = None
current_count = 0
current_rating = 0
product_id = None
rating = None

for line in sys.stdin:
    line = line.strip()
    product_id, rating = line.split('\t',1)

    try:
        rating = float(rating)
    except ValueError:
        continue

    if current_product == product_id:
        current_count += 1
        current_rating += rating
    else:
        if current_product:
            print('{}\t{}\t{}'.format(current_product,current_count,round(current_rating/current_count, 1)))
        current_product = product_id
        current_count = 1
        current_rating = rating


if current_product == product_id:
    print('{}\t{}'.format(current_product,current_rating))
