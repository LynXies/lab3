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
    cursor.execute("SELECT * FROM links")
    result = cursor.fetchall()
    output = template('interface', result=result)
    print(result)
    conn.commit()

    return output


def add_data(df):
    add = df.to_sql('links', conn, if_exists='replace')
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
    if request.GET.parse:
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
        print(len(df))
        conn.commit()

    return template('crawler.tpl')


@route('/insert', method='GET')
def insert():
    if request.GET.save:
        id = str(cursor.lastrowid+1)
        href = request.GET.href.strip()
        title = request.GET.title.strip()
        cursor.execute("INSERT INTO links VALUES(?,?,?)", (id, href, title))
        new_id = cursor.lastrowid

        conn.commit()

        return '<p>>The new task was inserted into the database, the ID is %s</p>' % new_id
    else:
        return template('new_task.tpl')


@ route('/update/<no:int>', method='GET')
def update_item(no):
    if request.GET.save:
        href = request.GET.href.strip()
        title = request.GET.title.strip()
        cursor.execute(
            "UPDATE links SET href = ?, title = ? WHERE id LIKE ?", (href, title, no))
        conn.commit()

        return '<p>The item number %s was successfully updated</p>' % no
    else:
        cursor.execute("SELECT * FROM links WHERE id LIKE ?", str((no)))
        cur_data = cursor.fetchone()
        print(cur_data)

        return template('edit_task', old=cur_data, no=no)


@ route('/delete/<no:int>', method="GET")
def delete_item(no):
    cursor.execute("SELECT count(*) FROM links")
    cursor.execute("DELETE FROM links WHERE id=?", str(no))
    cursor.execute("SELECT count(*) FROM links")
    conn.commit()
    return '<p>The item number %s was successfully deleted</p>' % no


run(host='localhost', port=8080, debug=True)
