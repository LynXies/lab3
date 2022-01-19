import sqlite3
from bottle import route, run, debug, template, request
import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
url = 'https://xakep.ru/'
headers = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
           "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
           "sec-ch-ua": "\"Google Chrome\";v=\"95\", \"Chromium\";v=\"95\", \";Not A Brand\";v=\"99\"",
           "sec-ch-ua-mobile": "?0",
           "sec-ch-ua-platform": "\"Windows\"",
           "sec-fetch-dest": "document",
           "sec-fetch-mode": "navigate",
           "sec-fetch-site": "same-origin",
           "sec-fetch-user": "?1",
           "upgrade-insecure-requests": "1",
           "cookie": "_ga=GA1.2.737393603.1634229632; __gads=ID=8f33bcf4f46c6739:T=1634229641:S=ALNI_MamWgAseKX7uBYtPWn-A7fpsXAY1Q; _ym_uid=1634229749562852097; _ym_d=1634229749; wordpress_logged_in_95a2ce14874d444647baa643165aaf19=Doctor_wHo_Try%7C1637264911%7CrRX7rfJMO5U2cpBYsboiWgrCgyYJQGqYmCVrWg72aVY%7C080f019e9f45e3d770bef2f97b063c7c145d0e17095481cc29ab15ae2ed27b09; _gid=GA1.2.144395574.1636783796; _gat=1",
           "Referer": "https://xakep.ru/",
           "Referrer-Policy": "strict-origin-when-cross-origin"
           }
conn = sqlite3.connect('lab.db')
cursor = conn.cursor()


@route('/select')
def select():
    cursor.execute("SELECT * FROM links GROUP BY title, href")
    result = cursor.fetchall()
    output = template('interface', result=result)
    print(result)

    return output


def add_data(df):
    add = df.to_sql('links', conn, if_exists='append')
    if (add):
        print("Данные успешно добавлены")

    return add


@route('/crawler', method='GET')
def crawler():
    hs = []
    hrefs = []
    spans = []
    tags = []
    n_pages = 0
    if request.GET.save:
        first = int(request.GET.first.strip())
        last = int(request.GET.last.strip())
        for page in range(first, last):
            url = 'https://xakep.ru/page/'+str(page)
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.content, 'html.parser')
            h = soup.find_all("h3", {"class": "entry-title"})
            for el in h:
                hs.append(el)
            for h in hs:
                article_hrefs = h.find_all('a')
                for tag in article_hrefs:
                    href = tag['href']
                    hrefs.append(href)
                    t = tag.select('a > span')
                    tags.append(t)
            n_pages += 1

        flatten_tags = [item for sublist in tags for item in sublist]
        for elem in flatten_tags:
            el = elem.text
            spans.append((el))
        print(len(spans))
        print(len(hrefs))

        cols = ['href', 'title']
        df = pd.DataFrame({'href': hrefs,
                           'title': spans})[cols]

        add_data(df)

    return template('crawler.tpl')


run(host='localhost', port=8080, debug=True)
