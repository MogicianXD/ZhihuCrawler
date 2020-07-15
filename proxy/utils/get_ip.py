import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def init_ip_file(pagenum=4):

    ua = UserAgent()

    encoding = 'utf-8'
    s = requests.session()
    s.keep_alive = False

    http_list = []
    https_list = []
    root = 'https://www.xicidaili.com/nn/'
    for i in range(pagenum):
        r = s.get(root + str(pagenum+1), headers={'User-Agent': ua.random})
        r.encoding = encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find('table', {'id': 'ip_list'})
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            if tds:
                ip = tds[1].string
                port = tds[2].string
                protocol = tds[5].string
                if protocol == 'HTTP':
                    http_list.append('http://' + ip + ':' + port)
                elif protocol == 'HTTPS':
                    https_list.append('https://' + ip + ':' + port)

    with open('http_list.txt', 'w+', encoding=encoding) as f:
        f.write('\n'.join(http_list))

    with open('https_list.txt', 'w+', encoding=encoding) as f:
        f.write('\n'.join(https_list))


