import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3

def countries_over_100B():
    sql1 = 'SELECT Country, GDP_USD_billion FROM Countries_by_GDP \
    WHERE GDP_USD_billion >= 100'

    # SQL 실행
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

    sql3 = "SELECT 'African', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE african = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'Arab', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE arab = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'Asia Pacific', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE ap = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'Latin', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE latin = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'North America', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE na = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'Oceanian', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE oceanian = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5) \
            UNION ALL \
            SELECT 'Europe', ROUND(AVG(GDP_USD_billion), 2) \
            FROM (SELECT GDP_USD_billion FROM Countries_by_GDP \
                    WHERE europe = 1 \
                    ORDER BY GDP_USD_billion DESC LIMIT 5)"
    

    regions_str = ['african', 'arab', 'ap', 'latin', 'na' ,'oceanian', 'europe']

    # SQL 실행
    with sqlite3.connect('World_Economies.db') as conn:
        cursor = conn.cursor()

        # 함수와 반복문을 통한 SQL 실행.
        # for region in regions_str:
        #     cursor.execute(sql2(region))
        #     rows = cursor.fetchall()

            # for row in rows:
            #     print(row)

        # 단일 SQL 문장을 통한 실행.
        cursor.execute(sql3)
        rows = cursor.fetchall()

        for row in rows:
            print(row)
    
    print()


if __name__=='__main__':
    countries_over_100B()
    region_averages()