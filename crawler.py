from fake_useragent import UserAgent
from proxy.client import ProxyFetcher
from proxy.utils import get_redis_conn

from zhihu_login import *

user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
headers = {'accept-language': 'zh-CN,zh;q=0.9',
           'Host': 'www.zhihu.com',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
           }


class Crawler:
    timeout = 10
    success_req = 'zhihu:success:request'
    cur_time = 'zhihu:success:time'

    def __init__(self, captcha_model, account: ZhihuAccount, proxy_mode=1, retries=1):
        self.captcha_model = captcha_model
        self.account = account
        self.proxy_mode = proxy_mode
        self.retries = retries
        self.fetcher = ProxyFetcher('zhihu', strategy='robin', length=5)
        self.conn = get_redis_conn(db=1)
        self.ua = UserAgent(verify_ssl=False)
        self.session = requests.session()
        self.HTMLSession = HTMLSession()
        self.account.login()
        self.set_cookies(self.account.session.cookies)

    def get(self, url, referer, use_html=False, fake=True):
        proxy = None
        resp = None
        tries = 0
        while tries < self.retries:
            if self.proxy_mode:
                proxy = self.fetcher.get_proxy()
                while not proxy:
                    print('no available proxy')
                    time.sleep(5)
                    proxy = self.fetcher.get_proxy()
                proxy = {'http': proxy}

            try:
                start = time.time() * 1000
                if use_html:
                    resp = self.get_with_request_html(url, referer, proxy)
                    end = time.time() * 1000
                    if 'signin' in resp.html.url:
                        while not self.account.login():
                            print('登陆失败')
                        resp = self.get_with_request_html(url, referer, proxy)
                    while 'unhuman' in resp.html.url:
                        resp = self.appeal(url)
                else:
                    resp = self.get_with_request(url, referer, proxy, fake)
                    end = time.time() * 1000
                    while '验证' in resp.text:
                        resp = self.appeal(url)
                if resp.status_code != 200:
                    # self.fetcher.proxy_feedback('failure')
                    tries += 1
                    continue
                else:
                    print('Request succeeded! The proxy is {}'.format(proxy))
                    # if you use greedy strategy, you must feedback
                    self.fetcher.proxy_feedback('success', int(end - start))
                    # not considering transaction
                    self.conn.incr(self.success_req, 1)
                    self.conn.rpush(self.cur_time, int(end / 1000))
                    return resp
            except Exception as e:
                print(str(e))
                # it's important to feedback, otherwise you may use the bad proxy next time
                self.fetcher.proxy_feedback('failure')
                tries += 1
        print("retries exceeded")
        return resp

    def get_with_request(self, url, referer, proxy, fake=True):
        if fake:
            agent = self.ua.random
        else:
            agent = user_agent
        return self.session.get(url, headers={"User-Agent": agent,
                                              'accept-language': 'zh-CN,zh;q=0.9',
                                              'Host': 'www.zhihu.com',
                                              "referer": referer}
                                , proxies=proxy, timeout=self.timeout)

    def get_with_request_html(self, url, referer, proxy):
        return self.HTMLSession.get(url, headers={"User-Agent": requests_html.user_agent(),
                                                  'Host': 'www.zhihu.com',
                                                  "referer": referer}
                                    , proxies=proxy, timeout=self.timeout)

    def set_cookies(self, cookies):
        self.HTMLSession.cookies = cookies
        self.session.cookies = cookies

    def appeal(self, url):

        r = self.HTMLSession.get('https://www.zhihu.com/api/v4/anticrawl/captcha_appeal')
        captchaUrl = r.json()['img_base64']
        captchaUrl = re.sub('\n', '', captchaUrl)
        with open('cache/captcha2.png', 'wb') as f:
            img_base64 = base64.b64decode(captchaUrl.strip('data:image/png;base64,').strip())
            print(img_base64)
            f.write(img_base64)
        im = Image.open('cache/captcha2.png')
        captcha = self.captcha_model.recgImg(im)
        print(captcha)

        r = self.HTMLSession.post('https://www.zhihu.com/api/v4/anticrawl/captcha_appeal',
                                  data=json.dumps({"captcha": captcha}),
                                  headers={"User-Agent": user_agent,
                                           "referer": 'https://www.zhihu.com/account/unhuman?type=unhuman&message=%E7%B3%BB%E7%BB%9F%E7%9B%91%E6%B5%8B%E5%88%B0%E6%82%A8%E7%9A%84%E7%BD%91%E7%BB%9C%E7%8E%AF%E5%A2%83%E5%AD%98%E5%9C%A8%E5%BC%82%E5%B8%B8%EF%BC%8C%E4%B8%BA%E4%BF%9D%E8%AF%81%E6%82%A8%E7%9A%84%E6%AD%A3%E5%B8%B8%E8%AE%BF%E9%97%AE%EF%BC%8C%E8%AF%B7%E8%BE%93%E5%85%A5%E9%AA%8C%E8%AF%81%E7%A0%81%E8%BF%9B%E8%A1%8C%E9%AA%8C%E8%AF%81%E3%80%82&need_login=false',
                                           'Content-Type': 'application/json',
                                           'x-xsrftoken': self.HTMLSession.cookies._cookies['.zhihu.com']['/']['_xsrf'].value})
        return self.HTMLSession.get(url, allow_redirects=False)
