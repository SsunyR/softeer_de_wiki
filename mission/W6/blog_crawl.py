import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from multiprocessing import Pool, cpu_count, set_start_method
import csv
import time
import sys
import re

# Windows에서 'spawn' 방식으로 멀티프로세싱을 시작하도록 명시
if sys.platform.startswith('win'):
    try:
        set_start_method('spawn', force=True)
    except RuntimeError:
        pass

# 블로그 ID 설정
blog_id = 'hdshin7'

# 셀레니움 드라이버 초기화 함수 (멀티프로세싱에 맞게 각 함수 내에서 생성)
def get_driver():
    """
    제공된 옵션으로 Selenium 드라이버를 초기화하는 함수입니다.
    멀티프로세싱의 각 자식 프로세스에서 호출됩니다.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # 드라이버 객체 생성
    return webdriver.Chrome(options=options)

def get_total_posts(driver, blog_id):
    """
    Selenium을 사용하여 블로그의 전체 게시글 수를 파악합니다.
    """
    driver.get(f'https://blog.naver.com/{blog_id}')
    try:
        # iframe으로 전환
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        
        # '총 게시글' 텍스트를 포함하는 strong 태그를 찾음
        total_post_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//strong[contains(text(), '총 게시글')]"))
        )
        total_posts_text = total_post_element.text.strip().replace(',', '')
        
        # 정규표현식을 사용하여 숫자만 추출
        match = re.search(r'\d+', total_posts_text)
        if match:
            return int(match.group())
        else:
            print("게시글 텍스트에서 숫자를 찾을 수 없습니다.")
            return 0
    except Exception as e:
        print(f"총 게시글 수 파악 실패: {e}")
        return 0
    finally:
        driver.switch_to.default_content() # 원래 프레임으로 전환

def get_page_urls_for_scraping(blog_id, total_posts):
    """
    전체 게시글 수를 바탕으로 모든 페이지의 URL 목록을 생성합니다.
    """
    base_url = f"https://blog.naver.com/PostList.naver?blogId={blog_id}"
    num_pages = (total_posts // 10) + 1
    page_urls = []
    for page_num in range(1, num_pages + 1):
        prev_page_num = ((page_num - 1) // 10) * 10 + 1
        url = f"{base_url}&currentPage={page_num}&prevPage={prev_page_num}"
        page_urls.append(url)
    return page_urls

def get_post_urls_from_page(page_url):
    """
    주어진 페이지 URL에서 모든 게시글의 URL을 추출합니다.
    """
    driver = get_driver()
    try:
        print(f"게시글 URL 수집 중: {page_url}")
        driver.get(page_url)
        
        # 게시글 링크가 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="logNo"]'))
        )
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        post_urls = []
        links = soup.find_all('a', href=re.compile(r'logNo=\d+'))
        for link in links:
            href = link.get('href')
            if href and 'logNo=' in href:
                full_url = f"https://blog.naver.com{href}"
                post_urls.append(full_url)
        
        return list(set(post_urls))
    except (NoSuchElementException, TimeoutException) as e:
        print(f"페이지 로드 실패 또는 요소 찾기 실패: {page_url}, 에러: {e}")
        return []
    except Exception as e:
        print(f"예기치 않은 오류 발생: {page_url}, 에러: {e}")
        return []
    finally:
        driver.quit()

def scrape_post_data(post_url):
    """
    단일 게시글의 제목, 날짜, 본문 내용을 스크래핑합니다.
    """
    driver = get_driver()
    try:
        print(f"스크래핑 중: {post_url}")
        driver.get(post_url)
        
        # 게시글 제목이 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.p-title h3'))
        )
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        title = ""
        title_tag = soup.find('div', class_='p-title')
        if title_tag:
            h3_tag = title_tag.find('h3')
            if h3_tag:
                title = h3_tag.text.strip()
        
        date = ""
        date_tag = soup.find('span', class_='se_publishDate')
        if date_tag:
            date = date_tag.text.strip()
        
        content = ""
        content_area = soup.find('div', id='postViewArea')
        if content_area:
            content_text_parts = [p.text.strip() for p in content_area.find_all('p') if p.text.strip()]
            content = ' '.join(content_text_parts)

        return {'title': title, 'date': date, 'content': content, 'url': post_url}
    except (NoSuchElementException, TimeoutException) as e:
        print(f"게시글 로드 실패 또는 요소 찾기 실패: {post_url}, 에러: {e}")
        return None
    except Exception as e:
        print(f"예기치 않은 오류 발생: {post_url}, 에러: {e}")
        return None
    finally:
        driver.quit()

def save_to_csv(data, filename='blog_posts.csv'):
    """
    스크래핑된 데이터를 CSV 파일로 저장합니다.
    """
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"데이터가 '{filename}' 파일에 성공적으로 저장되었습니다.")

if __name__ == '__main__':
    start_time = time.time()

    # 이 부분은 멀티프로세싱을 사용하지 않고 메인 프로세스에서만 실행됩니다.
    main_driver = get_driver()
    total_posts = get_total_posts(main_driver, blog_id)
    main_driver.quit()
    
    if total_posts == 0:
        print("총 게시글 수를 찾을 수 없어 스크래핑을 중단합니다.")
        sys.exit(1)
        
    print(f"총 게시글 수: {total_posts}개")
    
    page_urls = get_page_urls_for_scraping(blog_id, total_posts)
    
    print("페이지별 게시글 URL 목록을 수집 중...")
    post_urls = []
    
    with Pool(cpu_count()) as pool:
        urls_from_pages = pool.map(get_post_urls_from_page, page_urls)
    
    for urls in urls_from_pages:
        post_urls.extend(urls)
    
    post_urls = list(set(post_urls))
    print(f"총 {len(post_urls)}개의 고유한 게시글 URL을 찾았습니다.")
    
    print("게시글 데이터를 스크래핑 중...")
    scraped_data = []
    
    with Pool(cpu_count()) as pool:
        results = pool.map(scrape_post_data, post_urls)
    
    scraped_data = [result for result in results if result]
    
    if scraped_data:
        save_to_csv(scraped_data)
    else:
        print("스크래핑된 데이터가 없습니다.")
    
    end_time = time.time()
    print(f"총 소요 시간: {end_time - start_time:.2f}초")
