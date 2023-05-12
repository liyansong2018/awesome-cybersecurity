'''
Author: liyansong2018
Version: 1.1
Date: 2023-05-12
Description: github modify json api
Caution: You have exceeded a secondary rate limit.
- User-to-server requests are limited to 5,000 requests per hour and per authenticated user.
- For unauthenticated requests, the rate limit allows for up to 60 requests per hour.
Reference
https://docs.github.com/en/developers/apps/building-github-apps/rate-limits-for-github-apps
'''

# -*- coding: UTF-8 -*-

import requests
import urllib3
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
    if github_disc != None:
        # ...->…
        pattern = r'(\<.*?\>)|…'
        disc = re.sub(pattern, '', github_disc)
        return disc.strip()
    else:
        return github_disc

def main(keywords, page_number, star_number, cookie, proxies=None):
    if len(sys.argv) <= 1:
        print('<usage>: %s [file.csv]')
        exit(-1)

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-encoding': 'gzip, deflate, br',
        'Accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-control': 'max-age=0',
        'Cookie': cookie,       # Your cookie
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
    has_id = []
    for keyword in keywords:
        for i in range(page_number):
            url = 'https://github.com/search?p={}&q={}&type=Repositories'.format(i + 1, keyword)
            # github-error-rate-limit-exceeded
            response = requests.get(url=url, headers=headers, proxies=proxies, verify=False)
            soup = BeautifulSoup(response.text, 'lxml')
            application_json = soup.find_all('script', attrs={'type': 'application/json', 'data-target': 'react-app.embeddedData'})[0]
            dict = json.loads(application_json.get_text())
            if dict['payload']['results'] == None:
                break

            for item in dict['payload']['results']:
                print(item)
                id = item['id']
                name = item['repo']['repository']['name']
                user = item['repo']['repository']['owner_login']
                discription = item['hl_trunc_description']
                star = item['followers']
                update_time = item['repo']['repository']['updated_at']
                year = float(update_time[:4])
                repo_url = 'https://github.com/{}/{}'.format(user, name)

                if id not in has_id and star >= star_number:
                    has_id.append(id)
                else:
                    break

                repo.append(
                    {
                        'id': id,
                        'name': name,
                        'user': user,
                        'discription': handle_disc(discription),
                        'star': star,
                        'update time': update_time,
                        'year': year,
                        'url': repo_url
                    })

    head = ['id', 'name', 'user', 'discription', 'star', 'update time', 'year', 'url']
    with open(sys.argv[1], 'w', newline='', encoding='utf-8') as fp:
        fp_csv = csv.DictWriter(fp, head)
        fp_csv.writeheader()
        fp_csv.writerows(repo)

if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    cookie = '' # Your github account cookie!
    proxies = {
        "http": "http://localhost:10809",
        "https": "http://localhost:10809",
    }
    keywords = ['awesome-security', 'awesome_cybersecurity']
    page_number = 20
    star_number = 10

    main(keywords, page_number, star_number, cookie, proxies)

