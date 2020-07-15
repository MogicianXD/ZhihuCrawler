import pandas as pd
from db import ZhihuDB
import jieba
import jieba.analyse
import jieba.posseg
from wordcloud import WordCloud
from PIL import Image
import numpy as np
import csv
from tqdm import tqdm
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import networkx as nx

db = ZhihuDB()


def get_stopwords(filepath='res/stopwords_zhihu.txt'):
    stopwords = set([line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()])
    return stopwords


def cut():
    stopwords = get_stopwords()
    sql = """
    SELECT title 
    FROM question 
    """
    frequencies = dict()
    for title in tqdm(db.fetch_all(sql)):
        # text += ' '.join(set(jieba.cut(title[0])) - stopwords) + ' '
        # text += ' '.join(jieba.analyse.extract_tags(title[0], allowPOS=('n'))) + ' '
        for token in jieba.posseg.cut(title[0]):
            if token.flag[0] != 'n':
                continue
            if token not in frequencies:
                frequencies[token] = 1
            else:
                frequencies[token] += 1

    with open('cut_tmp.csv', 'w+', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['word', 'flag', 'freq'])
        for token, freq in frequencies.items():
            writer.writerow([token.word, token.flag, freq])


def word_cloud():
    stopwords = get_stopwords()
    df_n = pd.read_csv('cut_tmp.csv')
    df_n = df_n[~df_n['word'].isin(stopwords)]
    df_nr = df_n[df_n['flag'] == 'nr']
    df_ns = df_n[df_n['flag'] == 'ns']
    dfs = {'n': df_n, 'nr': df_nr, 'ns': df_ns}
    # texts = {'n': '', 'nr': '', 'ns': ''}
    dicts = {'n': dict(), 'nr': dict(), 'ns': dict()}
    for key in dfs.keys():
        dfs[key] = dfs[key][['word', 'freq']].groupby('word').sum()
        dicts[key] = dict([(index, freq) for index, freq in zip(dfs[key].index, dfs[key].freq)])
    font = 'res/canger02_W03.ttf'
    mask = np.array(Image.open('res/刘看山.png'))
    wc = WordCloud(
        background_color='white',
        mask=mask,  # 若没有该项，则生成默认图片
        font_path=font,  # 中文分词必须有中文字体设置
        stopwords=stopwords
    )
    for key in dicts.keys():
        wc.generate_from_frequencies(dicts[key])  # 绘制图片
        wc.to_file('output/qu_wordcloud_' + key + '.png')  # 保存图片


def compute_avg_and_max():
    table = PrettyTable([' ', 'avg_num', 'max_num', 'name_of_the_max (question or usr)'])
    avg_sql = 'SELECT avg({}) FROM {}'
    avg_sql2 = 'SELECT avg(count({*})) FROM {1} GROUP BY {0}'
    max_sql1 = 'SELECT {0}, {1} FROM {2} ORDER BY {0} DESC LIMIT 1'
    max_sql2 = '''
    SELECT max_num, {0} 
    FROM (
        SELECT {1}, {2} as max_num 
        FROM {3} 
        ORDER BY {2} DESC 
        LIMIT 1
        ) as t NATURAL JOIN {4}  
    '''
    max_vote, max_vote_qu_title = db.fetch_one(max_sql2.format('title', 'qid', 'vote_num', 'answer', 'question'))
    max_cmt, max_cmt_qu_title = db.fetch_one(max_sql2.format('title', 'qid', 'comment_num', 'answer', 'question'))
    max_ans, max_ans_title = db.fetch_one(max_sql1.format('answer_count', 'title', 'question'))
    max_flw, max_flw_title = db.fetch_one(max_sql1.format('follower_count', 'title', 'question'))
    max_toc, max_toc_title = db.fetch_one(max_sql2.format('title', 'tid', 'count(tid)', 'follow_topic', 'tid'))
    max_con, max_con_usr = db.fetch_one(max_sql2.format('uname', 'uid', 'contribution', 'follow_topic', 'uid'))
    max_usr_ans, max_usr_ans_name = db.fetch_one(max_sql1.format('answer_count', 'uname', 'usr'))
    max_usr_flw, max_usr_flw_name = db.fetch_one(max_sql1.format('follower_count', 'uname', 'usr'))
    max_usr_art, max_usr_art_name = db.fetch_one(max_sql1.format('articles_count', 'uname', 'usr'))

    table.add_row(['答案赞同数',
                   db.fetch_one(avg_sql.format('vote_num', 'answer'))[0],
                   max_vote, max_vote_qu_title])
    table.add_row(['答案评论数',
                   db.fetch_one(avg_sql.format('comment_num', 'answer'))[0],
                   max_cmt, max_cmt_qu_title])
    table.add_row(['问题回答数',
                   db.fetch_one(avg_sql.format('answer_count', 'question'))[0],
                   max_ans, max_ans_title])
    table.add_row(['问题关注数',
                   db.fetch_one(avg_sql.format('follower_count', 'question'))[0],
                   max_flw, max_flw_title])
    table.add_row(['话题关注数',
                   db.fetch_one(avg_sql.format('tid', 'follow_topic'))[0],
                   max_toc, max_toc_title])
    table.add_row(['话题贡献数',
                   db.fetch_one(avg_sql.format('contibution', 'follow_topic'))[0],
                   max_con, max_con_usr])
    table.add_row(['用户回答数',
                   db.fetch_one(avg_sql.format('answer_count', 'usr'))[0],
                   max_usr_ans, max_usr_ans_name])
    table.add_row(['用户关注数',
                   db.fetch_one(avg_sql.format('follower_count', 'usr'))[0],
                   max_usr_flw, max_usr_flw_name])
    table.add_row(['用户文章数',
                   db.fetch_one(avg_sql.format('articles_count', 'usr'))[0],
                   max_usr_art, max_usr_art_name])

    print(table)


# def plot_count_num(table_name, count_col):
#     sql = '''
#     SELECT {0}, count(*) as cnt
#     FROM {1}
#     GROUP BY {0}
#     '''
#     df = pd.read_sql(sql.format(count_col, table_name), con=db.conn, index_col=[count_col])
#     figure = df.plot()
#     plt.title(count_col + ' of ' + table_name)
#     plt.xlabel(count_col)
#     plt.ylabel('count')
#     plt.show()
#
#
# def plot_all_count_num():
#     for table_name, count_col in [('question', 'answer_count'),
#                                   ('question', 'follower_count'),
#                                   ('answer', 'vote_num'),
#                                   ('answer', 'comment_num'),
#                                   ('usr', 'answer_count'),
#                                   ('usr', 'follower_count'),
#                                   ('usr', 'articles_count')]:
#         plot_count_num(table_name, count_col)


def date_analyse():
    sql_qu = '''
    SELECT from_unixtime(create_time, '%Y-%m') AS month, count(*) AS question_count
    FROM question
    GROUP BY from_unixtime(create_time, '%Y-%m')
    '''
    sql_ans = '''
    SELECT from_unixtime(create_time, '%Y-%m') AS month, count(*) AS answer_count
    FROM answer
    GROUP BY from_unixtime(create_time, '%Y-%m')
    '''
    df_qu = pd.read_sql(sql_qu, db.conn, index_col='month')
    df_ans = pd.read_sql(sql_ans, db.conn, index_col='month')
    print(df_ans.head)
    df = df_qu.join(df_ans, how='outer').fillna(0)
    df = df[df.index < '2019-11']
    df.plot(title='create_num per month')
    plt.show()


def time_analyse():
    sql_qu = '''
    SELECT from_unixtime(create_time, '%H:%i') AS clock, count(*) AS question_count
    FROM question
    GROUP BY from_unixtime(create_time, '%H:%i')
    '''
    sql_ans = '''
    SELECT from_unixtime(create_time, '%H:%i') AS clock, count(*) AS answer_count
    FROM answer
    GROUP BY from_unixtime(create_time, '%H:%i')
    '''
    df_qu = pd.read_sql(sql_qu, db.conn, index_col='clock')
    df_ans = pd.read_sql(sql_ans, db.conn, index_col='clock')
    df = df_qu.join(df_ans, how='outer').fillna(0)
    df.plot(title='create_num per minute')
    plt.show()


def gender_analyse():
    sql = '''
    SELECT 
        CASE gender
            WHEN 0 THEN 'male'
            WHEN 1 THEN 'female'
            WHEN -1 THEN 'unknown'
        END as gender
    , count(*) AS num
    FROM usr
    GROUP BY gender
    '''
    df = pd.read_sql(sql, db.conn, index_col='gender')
    df.plot(kind='pie', title='gender distribution', y='num', autopct='%.2f')
    plt.gca().legend_.remove()
    plt.show()


    sql = '''
    SELECT a.gender1, b.gender as gender2, count(*) as num
    FROM (
        SELECT gender as gender1, follower
        FROM usr NATURAL JOIN follow ) as a 
        JOIN usr as b on a.follower = b.uid
    GROUP BY gender1, gender2
    '''
    df = pd.read_sql(sql, db.conn)
    df['gender2'] = df['gender2'].apply(lambda x: 'male' if x == 0 else ('female' if x == 1 else 'unknown'))
    df_male = df[df['gender1'] == 0][['gender2', 'num']].set_index('gender2')
    df_female = df[df['gender1'] == 1][['gender2', 'num']].set_index('gender2')
    df_male.plot(kind='pie', title='The distribution of man\'s follower', y='num', autopct='%.2f')
    plt.gca().legend_.remove()
    plt.show()
    df_female.plot(kind='pie', title='The distribution of woman\'s follower', y='num', autopct='%.2f')
    plt.gca().legend_.remove()
    plt.show()


def autolabel(rects, xpos='center'):
    """
    Attach a text label above each bar in *rects*, displaying its height.

    *xpos* indicates which side to place the text w.r.t. the center of
    the bar. It can be one of the following {'center', 'right', 'left'}.
    """

    xpos = xpos.lower()  # normalize the case of the parameter
    ha = {'center': 'center', 'right': 'left', 'left': 'right'}
    offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

    for rect in rects:

        height = rect.get_height()
        #         print(height)
        if height / 1000 < 0.1:
            continue

        plt.text(rect.get_x() + rect.get_width() * offset[xpos], 1.01 * height,
                 '{}k'.format(int(height / 1000)), ha=ha[xpos], va='bottom')


def six_degrees_space():
    sql = '''
    SELECT * FROM follow AS a
    WHERE EXISTS (
			SELECT * FROM follow AS b 
            WHERE a.follower = b.uid )
    '''
    df = pd.read_sql(sql, db.conn)
    g = nx.from_pandas_edgelist(df, source='uid', target='follower')

    count_dic = dict()
    i, sum = 0, g.number_of_nodes()
    for node in g:
        lens = nx.single_source_shortest_path_length(g, node)
        for length in lens.values():
            if length not in count_dic:
                count_dic[length] = 1
            else:
                count_dic[len] += 1
    i += 1
    print('\r%d/%d'%(i, sum), end='')

    del count_dic[0]
    plt.figure(figsize=(7, 6))
    fig = plt.bar(x=count_dic.keys(), height=count_dic.values())
    autolabel(fig)



if __name__ == '__main__':
    # cut()
    # word_cloud()
    # compute_avg_and_max()
    gender_analyse()
