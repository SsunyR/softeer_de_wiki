#!/usr/bin/env python3

import sys

for line in sys.stdin:
    line = line.strip()
    fields = line.split(sep=',')
    sentiment_num = fields[0].strip('"')

    # 0 = negative, 2 = neutral, 4 = positive
    if sentiment_num == '0':
        sentiment = 'negative'
    elif sentiment_num == '2':
        sentiment = 'neutral'
    elif sentiment_num == '4':
        sentiment = 'positive'
    else:
        continue

    print('{}\t{}'.format(sentiment, 1))