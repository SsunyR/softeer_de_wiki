#!/usr/bin/env python3

import sys
import re

for line in sys.stdin:
    line = re.sub(r'\W+',' ',line.strip())
    words = line.split()

    for word in words:
        word = word.lower()
        print('{}\t{}'.format(word,1))
