from multiprocessing import Process
from db import *
from zhihu_captcha import zhihu_captcha

from crawler import *

headers = {'accept-language': 'zh-CN,zh;q=0.9',
           'Host': 'www.zhihu.com',
           'Upgrade-Insecure-Requests': '1',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

followers_api = "https://www.zhihu.com/api/v4/members/{}/followers?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics\u0026offset={}\u0026limit=20"
followees_api = "https://www.zhihu.com/api/v4/members/{}/followees?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics\u0026offset={}\u0026limit=20"
follow_topic_api = "https://www.zhihu.com/api/v4/members/{}/following-topic-contributions?include=data%5B*%5D.topic.introduction&offset={}&limit=20"
answer_api = 'https://www.zhihu.com/api/v4/members/{}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Cexcerpt%2Cis_labeled%2Clabel_info%2Crelationship.is_authorized%2Cvoting%2Cis_author%2Cis_thanked%2Cis_nothelp%2Cis_recognized%3Bdata%5B*%5D.author.badge%5B%3F(type%3Dbest_answerer)%5D.topics%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20data%5B*%5D.question.has_publishing_draft%2Crelationship&offset={}&limit=20&sort_by=created'
question_api = 'https://www.zhihu.com/api/v4/questions/{}?include=data%5B*%5D.answer_count%2Cfollower_count%2Ctopics'

count = 0
crawl_dict = dict()


def begin_crawl_usr(crawler):
    try:
        while True:
            if len(crawl_dict) == 0:
                waits = db.get_wait()
                if len(waits) == 0:
                    break
                for wait in waits:
                    crawl_dict[wait[0]] = (wait[1], wait[2])
            data = crawl_dict.popitem()
            crawl_usr(crawler, data[0], data[1][0], data[1][1])
    except Exception as e:
        print(traceback.print_exc())
        ready_for_insert_wait = ((d[0], d[1][0], d[1][1]) for d in crawl_dict.items())
        db.insert_wait_many(ready_for_insert_wait)


def crawl_usr(crawler, uid, url_token, url):
    global count
    for i in range(2):
        crawl_url = followers_api if i == 0 else followees_api
        next_url = crawl_url.format(url_token, 0)
        if i == 0:
            referer = "{}/{}".format(url, 'followers')
        else:
            referer = "{}/{}".format(url, 'following')
        prev_url = referer
        pagenum = 0
        while True:
            res = crawler.get(next_url, prev_url)
            res.encoding = 'utf-8'
            json = res.json()
            pagenum += 1
            next_url = crawl_url.format(url_token, 20 * pagenum)
            prev_url = referer + "?page=" + str(pagenum)
            # time.sleep(random.random())
            for data in json['data']:
                exist = db.exist_usr(data['id'])
                if not exist:
                    db.insert_usr(data['id'], data['name'], data['url_token'], data['gender'], data['url'],
                                  data['answer_count'], data['articles_count'], data['follower_count'])
                if i == 0:
                    db.insert_follow(uid, data['id'])
                else:
                    db.insert_follow(data['id'], uid)
                if not exist:
                    if crawl_dict.get(data['id']) is None:
                        print('1', count)
                        count += 1
                        if len(crawl_dict) > 5000:
                            db.insert_wait(data['id'], data['url_token'], data['url'])
                        else:
                            crawl_dict[data['id']] = (data['url_token'], data['url'])
            if json['paging']['is_end']:
                break


def begin_crawl_follow_topic_and_answer(crawler):
    cnt = 0
    while True:
        usrs = db.get_usr()
        for usr in usrs:
            crawl_follow_topic(crawler, usr[0], usr[1], usr[2])
            if db.get_answer_count(usr[0])[0] > 0:
                crawl_answer_and_question(crawler, usr[0], usr[1], usr[2])
            db.insert_pass(usr[0])
            cnt += 1
            print('2', cnt)


def crawl_follow_topic(crawler, uid, utoken, url):
    next_url = follow_topic_api.format(utoken, 0)
    referer = '{}/{}'.format(url, 'following/topics')
    prev_url = referer
    pagenum = 0
    while True:
        res = crawler.get(next_url, prev_url)
        if res.status_code in [400, 401, 404, 410]:
            break
        elif res.status_code == 403:
            res = crawler.get(next_url, prev_url, True, False)
            if res.status_code in [400, 410, 404]:
                continue
        res.encoding = 'utf-8'
        json = res.json()
        pagenum += 1
        next_url = follow_topic_api.format(utoken, 20 * pagenum)
        prev_url = referer + "?page=" + str(pagenum)
        for data in json.get('data'):
            topic = data['topic']
            db.insert_topic(int(topic['id']), topic['name'])
            db.insert_follow_topic(uid, int(topic['id']), data['contributions_count'])
        if json['paging']['is_end']:
            break


def crawl_answer_and_question(crawler, uid, utoken, url):
    next_url = answer_api.format(utoken, 0)
    referer = '{}/{}'.format(url, 'answers')
    prev_url = referer
    pagenum = 0
    while True:
        res = crawler.get(next_url, prev_url)
        if res.status_code in [400, 404, 410]:
            break
        elif res.status_code in [401, 403]:
            res = crawler.get(next_url, prev_url, True, False)
            if res.status_code in [400, 401, 410, 404]:
                break
        res.encoding = 'utf-8'
        json = res.json()
        pagenum += 1
        next_url = answer_api.format(utoken, 20 * pagenum)
        prev_url = referer + "?page=" + str(pagenum)
        for data in json.get('data'):
            question = data['question']
            qid = question['id']
            db.insert_answer(data['id'], uid, qid, data['voteup_count'],
                             data['comment_count'], data['created_time'])

            # db.insert_question(qid, question['title'])
            if not db.exist_question(qid):
                # crawl_question(question, next_url, data['id'])
                crawl_question(crawler, qid, prev_url)

        if json['paging']['is_end']:
            break


def crawl_question(crawler, qid, referer):
    while True:
        try:
            res = crawler.get(question_api.format(qid), referer)
            if res.status_code in [400, 404, 410]:
                break
            elif res.status_code in [401, 403]:
                res = crawler.get(question_api.format(qid), referer, True, False)
                if res.status_code in [400, 401, 410, 404]:
                    break
            res.encoding = 'utf-8'
            question = res.json()
            db.insert_question(qid, question['title'], int(question['answer_count']),
                               int(question['follower_count']), question['created'])
            for topic in question['topics']:
                db.insert_topic(topic['id'], topic['name'])
                db.insert_tag(qid, topic['id'])
            break
        except Exception as e1:
            print(str(e1))
            time.sleep(1000)

'''
def crawl_question(crawler, question, referer, aid, use_html=False):
    qid = question['id']
    crawl_url = 'https://www.zhihu.com/question/{}/answer/{}'.format(qid, aid)
    # res.html.render()
    while True:
        try:
            res = crawler.get(crawl_url, referer, True, False)
            while 'sign' in res.html.url:
                if account.login(captcha_lang='en', load_cookies=True):
                    crawler.set_cookies(account.session.cookies)
                    res = crawler.get(crawl_url, referer, True)
            # res.html.render()
            answer_count = int(res.html.find('meta[itemprop=answerCount]', first=True).attrs['content'])
            follow_count = int(res.html.find('meta[itemprop=zhihu\:followerCount]', first=True).attrs['content'])
            db.insert_question(qid, question['title'], answer_count, follow_count, question['created'])
            topics = res.html.find('div.QuestionHeader-topics', first=True).find('span.Tag-content')
            for topic in topics:
                href = topic.find('a', first=True).attrs['href']
                tid = int(re.search('topic/(\d+)$', href).group(1))
                name = topic.find('div', first=True).text
                db.insert_topic(tid, name)
                db.insert_tag(qid, tid)
            break
        except Exception as e1:
            print(str(e1))
            time.sleep(1000)
'''

if __name__ == '__main__':
    ua = UserAgent()
    db = ZhihuDB()
    setting = json.load(open('setting.json'))
    captcha_model = zhihu_captcha.ZhihuCaptcha(str(setting['phone']), setting['password'])
    account = ZhihuAccount(captcha_model, str(setting['phone']), setting['password'])
    # init_ip_pool()
    # p1 = Process(target=begin_crawl_usr, args=(Crawler(captcha_model, account, retries=5), ))
    # p2 = Process(target=begin_crawl_follow_topic_and_answer, args=(Crawler(captcha_model, account, retries=5), ))
    # p1.start()
    # p2.start()
    crawler = Crawler(captcha_model, account, retries=2)
    begin_crawl_usr(crawler)
    begin_crawl_follow_topic_and_answer(crawler)
