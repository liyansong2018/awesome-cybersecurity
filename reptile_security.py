'''
Caution: You have exceeded a secondary rate limit.
- User-to-server requests are limited to 5,000 requests per hour and per authenticated user.
- For unauthenticated requests, the rate limit allows for up to 60 requests per hour.
Reference
https://docs.github.com/en/developers/apps/building-github-apps/rate-limits-for-github-apps
'''

# -*- coding: UTF-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import sys, csv

class Url:
    """
    Github repository link handle
    """
    pattern = r'[^/:]+'

    def __init__(self, url):
        self.url = url
        self.ret = re.findall(Url.pattern, url)

    def get_user(self):
        return self.ret[2]

    def get_repo(self):
        return self.ret[3]


def get_page(url, headers):
    """
    Get page number
    :param url: search url
    :param headers: requests headers
    :return: page number
    """
    response = requests.get(url=url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'lxml')
    page_sel = soup.select('#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0.codesearch-results > div > div.paginate-container.codesearch-pagination-container > div > em')
    return int(page_sel[0]['data-total-pages'])


def handle_star(github_star):
    """
    Get github repository star
    :param github_star: 1.1k or 100
    :return: 1100 or 100
    """
    pattern = r'[^k]+'
    star = re.findall(pattern, github_star)
    if github_star[-1] == 'k':
        return int(float(star[0]) * 1000)
    else:
        return int(star[0])


def handle_date(github_date):
    """
    Get github repository updated time distance from now
    :param github_date: repository updated time
    :return: time difference
    """
    now_stamp = int(time.time())
    update_time_array = time.strptime(github_date, '%Y-%m-%dT%H:%M:%SZ')
    update_time_stamp = int(time.mktime(update_time_array))
    dist_sec = now_stamp - update_time_stamp
    dist_time = {
        'year': dist_sec / (60 * 60 * 24 * 365),
        'month': dist_sec / (60 * 60 * 24 * 30),
        'day': dist_sec / (60 * 60 * 24),
        'hour': dist_sec / (60 * 60)
    }
    return dist_time


def handle_disc(github_disc):
    """
    Handle github repository description, .csv file can't handle special characters
    :param github_disc:
    :return:
    """
    pattern = r'[\w| |.|-]+'
    disc = re.findall(pattern, github_disc)
    return disc[0].strip()

def main():
    if len(sys.argv) <= 1:
        print('<usage>: %s [file.csv]')
        exit(-1)

    proxies = {
        "http": "http://localhost:1080",
        "https": "https://localhost:1080",
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-encoding': 'gzip, deflate, br',
        'Accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-control': 'max-age=0',
        'Cookie': '',       # Your cookie
        'if-none-match': 'W/"8c869a44ef95afccba0e45886711dbbf"',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Microsoft Edge";v="98"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56',
    }

    repo = []
    url = 'https://github.com/search?q=awesome-security'
    page = get_page(url, headers)
    for i in range(20):
        url = 'https://github.com/search?p={}&q=awesome-security&type=Repositories'.format(i + 1)
        # github-error-rate-limit-exceeded
        response = requests.get(url=url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'lxml')
        date = soup.findAll('relative-time')
        j = 0
        while True:
            j += 1
            proj = soup.select('#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0.codesearch-results > div > ul > li:nth-of-type({}) > div.mt-n1.flex-auto > div.d-flex > div > a'.format(j))
            disc = soup.select('#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0.codesearch-results > div > ul > li:nth-of-type({}) > div.mt-n1.flex-auto > p'.format(j))
            if proj == None or len(proj) == 0:
                break

            print(proj)
            data = json.loads(proj[0]['data-hydro-click'])
            repo_url = data['payload']['result']['url']
            url = Url(repo_url)
            repo_name = url.get_repo()
            repo_user = url.get_user()
            if disc != None and len(disc) > 0:
                repo_disc = disc[0].text.strip()
                star = soup.select(
                    '#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0.codesearch-results > div > ul > li:nth-of-type({}) > div.mt-n1.flex-auto > div:nth-child(3) > div.d-flex.flex-wrap.text-small.color-fg-muted > div:nth-child(1) > a'.format(
                        j))

            else:
                repo_disc = "NULL"
                star = soup.select(
                    '#js-pjax-container > div > div.col-12.col-md-9.float-left.px-2.pt-3.pt-md-0.codesearch-results > div > ul > li:nth-of-type({}) > div.mt-n1.flex-auto > div:nth-child(2) > div.d-flex.flex-wrap.text-small.color-fg-muted > div:nth-child(1) > a'.format(
                        j))

            if star != None and len(star) > 0:
                repo_star = star[0].text.strip()
            else:
                repo_star = '0'

            if date != None and len(date) > 0:
                repo_date = date[j - 1]['datetime']

            repo.append(
                {
                    'name': repo_name,
                    'user': repo_user,
                    'discription': handle_disc(repo_disc),
                    'star': handle_star(repo_star),
                    'update time': repo_date,
                    'distance': float(handle_date(repo_date)['year']),
                    'url': repo_url
                })

    head = ['name', 'user', 'discription', 'star', 'update time', 'distance', 'url']
    with open(sys.argv[1], 'w', newline='', encoding='utf-8') as fp:
        fp_csv = csv.DictWriter(fp, head)
        fp_csv.writeheader()
        fp_csv.writerows(repo)

if __name__ == '__main__':
    main()
