#!/usr/bin/env python3

import sys

current_movie = None
current_count = 0
current_rating = 0
movie_id = None
rating = None

for line in sys.stdin:
    line = line.strip()
    movie_id, rating = line.split('\t',1)

    try:
        rating = float(rating)
    except ValueError:
        continue

    if current_movie == movie_id:
        current_count += 1
        current_rating += rating
    else:
        if current_movie:
            print('{}\t{}'.format(current_movie.lstrip('0'),round(current_rating/current_count, 1)))
        current_movie = movie_id
        current_count = 1
        current_rating = rating


if current_movie == movie_id:
    print('{}\t{}'.format(current_movie,current_rating))
