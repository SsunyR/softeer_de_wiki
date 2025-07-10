import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

def countries_over_100B():
    sql1 = 'SELECT Country, GDP_USD_billion FROM Countries_by_GDP \
    WHERE GDP_USD_billion >= 100'

    with sqlite3.connect('World_Economies.db') as conn:
        cursor = conn.cursor()

        cursor.execute(sql1)
        rows = cursor.fetchall()

        for row in rows:
            print(row)

    print()

def region_averages():

    def sql2(region):
        return f'SELECT "{region.upper()}", ROUND(AVG(GDP_USD_billion), 2)\
            FROM (SELECT Country, GDP_USD_billion FROM Countries_by_GDP \
                    WHERE {region} = 1 \
                    ORDER BY GDP_USD_billion DESC \
                    LIMIT 5)'
    
    regions_str = ['african', 'arab', 'ap', 'latin', 'na' ,'oceanian', 'europe']
    
    with sqlite3.connect('World_Economies.db') as conn:
        cursor = conn.cursor()

        for region in regions_str:
            cursor.execute(sql2(region))
            rows = cursor.fetchall()

            for row in rows:
                print(row)
    
    print()


if __name__=='__main__':
    countries_over_100B()
    region_averages()