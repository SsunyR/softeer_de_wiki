import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


logging.basicConfig(
    filename="etl_project_log.txt",
    level=logging.INFO,
    format='%(asctime)s, %(message)s',
    datefmt='%Y-%B-%d-%H-%M-%S'
)

# Extract: url로부터 BeautifulSoup 객체 반환
def extract(url : str):
    
    print("Start Extraction")
    logger.info("Start Extraction")

    response = requests.get(url)
    if response.status_code != 200:
        print(response.status_code)
        raise Exception("Failed to load page")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

    print("End Extraction")
    logger.info("End Extraction")
    # BeautifulSoup 객체 반환
    return soup

# 테이블의 행들을 반환
def get_rows(soup : BeautifulSoup):
    table = soup.find('table', {'class':'wikitable'})
    rows = table.find_all('tr')

    return rows

# url로 IMF가 정한 region별 국가 리스트 추출하기.
def get_country_from_region(region : str):

    # Region별 url
    urls = {
        'african' : 'https://en.wikipedia.org/wiki/List_of_African_countries_by_GDP_(nominal)',
        'arab' : 'https://en.wikipedia.org/wiki/List_of_Arab_League_countries_by_GDP_(nominal)',
        'ap' : 'https://en.wikipedia.org/wiki/List_of_countries_in_Asia-Pacific_by_GDP_(nominal)',
        'latin' : 'https://en.wikipedia.org/wiki/List_of_Latin_American_and_Caribbean_countries_by_GDP_(nominal)',
        'na' : 'https://en.wikipedia.org/wiki/List_of_North_American_countries_by_GDP_(nominal)',
        'oceanian' : 'https://en.wikipedia.org/wiki/List_of_Oceanian_countries_by_GDP',
        'europe' : 'https://en.wikipedia.org/wiki/List_of_sovereign_states_in_Europe_by_GDP_(nominal)',
    }

    if(region not in urls.keys()):
        print("Region not avaiable.")
        print("Select from ['african', 'arab', 'ap', 'latin', 'na', 'oceanian', 'europe']")
        return

    response = requests.get(urls[region])
    if response.status_code != 200:
        print(response.status_code)
        raise Exception("Failed to load page")
    else:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table', {'class':'wikitable'})
    rows = table.find_all('tr')

    df = pd.read_json("Countries_by_GDP.json")
    countries = df['Country'].to_list()

    region_countries = []

    for row in rows:
        cols = row.find_all('a')
        for col in cols:
            country = col.get_text().strip()

            if country in countries:
                region_countries.append(country)
            
    return region_countries

# Transform: BeautifulSoup 객체로부터 전체 국가의 GDP를 USD_billion으로 나타낸 DataFrame 반환
def transform(soup : BeautifulSoup):

    print("Start Transformation")
    logger.info("Start Trasnformaion")

    rows = get_rows(soup)

    countries = []
    gdps = []
    regions_str = ['african', 'arab', 'ap', 'latin', 'na' ,'oceanian', 'europe']
    african = get_country_from_region('african')
    arab = get_country_from_region('arab')
    ap = get_country_from_region('ap')
    latin = get_country_from_region('latin')
    na = get_country_from_region('na')
    oceanian = get_country_from_region("oceanian")
    europe = get_country_from_region('europe')
    regions = [african, arab, ap, latin, na, oceanian, europe]
    isRegion = [[] for  i in range(len(regions))]

    for i, row in enumerate(rows):
        # 테이블 메타데이터
        if i in [0, 1, 2]:
            continue
        # 각 행의 열 정보들 리스트화
        cols = row.find_all('td')
        for j, col in enumerate(cols):
            # 국가 정보
            if j == 0:
                country = col.get_text(strip=True)
                countries.append(country)
                # 속한 region에 표시하기
                for k, region in enumerate(regions):
                    if(country in region):
                        isRegion[k].append(1)
                    else:
                        isRegion[k].append(0)

            # IMF의 GDP정보.
            if j == 1:
                content = col.get_text(strip=True)
                # IMF 미가입 국가
                if content == '—':
                    gdps.append(-1)
                else:
                    # GDP 정보 추출 후 USD billoin 단위로 변환
                    gdp = float(content.replace(',', ''))
                    gdp /= 1000
                    gdp = round(gdp, 2)
                    gdps.append(gdp)
    
    # Pandas DataFrame화
    df = pd.DataFrame({'Country':countries, 'GDP_USD_billion':gdps})
    # 각 Region 속성 추가
    for i, region in enumerate(regions_str):
        df[region] = isRegion[i]

    # IMF 미가입 국가의 데이터값 Not a Number로 변경
    df['GDP_USD_billion'] = df['GDP_USD_billion'].replace(-1, np.nan)

    # GDP 높은 순으로 정렬
    df = df.sort_values('GDP_USD_billion', ascending=False)

    print("End Transformation")
    logger.info("End Transformation")

    # 생성한 DataFrame 반환
    return df

# Load: DataFrame을 .json파일로 저장하고, DB에 테이블에 저장
def load(df : pd.DataFrame):

    print("Start Loading")
    logger.info("Start Loading")

    # 새 데이터 저장 전 이전 데이터 보관
    old_df = pd.read_json("Countries_by_GDP.json")
    old_df.to_json(f"Countries_by_GDP_{datetime.now()}_replaced.json", orient='records')

    # DF을 .json으로 저장
    df.to_json("Countries_by_GDP.json", orient='records')

    with sqlite3.connect('World_Economies.db') as conn:

        # 이미 테이블이 존재할 시 -> 기존 데이터 새 테이블에 저장? or 효율적으로 .json 파일 등으로 저장? -> 이름은 어떻게 처리?
        df.to_sql('Countries_by_GDP', conn, if_exists='replace', index=True)

        print("End Loading")
        logger.info("End Loading")


if __name__ == '__main__':
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29"
    
    soup = extract(url)

    df = transform(soup)

    load(df)
