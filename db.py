import pymysql
import traceback

class ZhihuDB:
    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1',
                                   user='root',
                                   password='root1037',
                                   db='zhihudata',
                                   charset='utf8')
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def execute(self, sql, args=None):
        try:
            self.cursor.execute(sql, args)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            # print(str(e))

    def executemany(self, sql, turples):
        try:
            self.cursor.executemany(sql, turples)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(str(e))

    def exist(self, table, id_name, id):
        sql = "SELECT {} FROM {} WHERE {} = %s".format(id_name, table, id_name)
        try:
            self.cursor.execute(sql, id)
            self.conn.commit()
            return self.cursor.fetchone() != None
        except:
            self.conn.rollback()
            print(traceback.format_exc())
            return False

    def exist_usr(self, uid):
        return self.exist('usr', 'uid', uid)

    def exist_question(self, qid):
        return self.exist('question', 'qid', qid)


    def insert_usr(self, uid, uname, utoken, gender, url, answer_count, articles_count, follower_count):
        sql = "INSERT INTO usr(uid, uname, utoken, gender, url, answer_count, articles_count, follower_count) " \
              "VALUE (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.execute(sql, (uid, uname, utoken, gender, url, answer_count, articles_count, follower_count))

    def insert_usr_many(self, turples):
        sql = "INSERT IGNORE INTO usr(uid, uname, utoken, gender, url, answer_count, articles_count, follower_count) " \
              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.executemany(sql, turples)

    def insert_follow(self, uid, follower):
        sql = "INSERT INTO follow(uid, follower) " \
              "VALUE (%s, %s)"
        self.execute(sql, (uid, follower))

    def insert_follow_many(self, turples):
        sql = "INSERT IGNORE INTO follow(uid, follower) " \
              "VALUES (%s, %s)"
        self.executemany(sql, turples)

    def insert_wait(self, uid, utoken, url):
        sql = "INSERT INTO wait(uid, utoken, url) " \
              "VALUE (%s, %s, %s)"
        self.execute(sql, (uid, utoken, url))

    def insert_wait_many(self, turples):
        sql = "INSERT IGNORE INTO wait(uid, utoken, url) " \
              "VALUES (%s, %s, %s)"
        self.executemany(sql, turples)

    def insert_pass(self, uid):
        sql = 'INSERT INTO pass VALUE (%s)'
        self.execute(sql, uid)

    def insert_question(self, qid, title, answer_count, follower_count, create_time):
        sql = 'INSERT INTO question(qid, title, answer_count, follower_count, create_time)' \
              'VALUE(%s, %s, %s, %s, %s)'
        self.execute(sql, (qid, title, answer_count, follower_count, create_time))

    def insert_answer(self, aid, uid, qid, vote_num, comment_num, create_time):
        sql = 'INSERT INTO answer(aid, uid, qid, vote_num, comment_num, create_time) ' \
              'VALUE (%s, %s, %s, %s, %s, %s)'
        self.execute(sql, (aid, uid, qid, vote_num, comment_num, create_time))

    def insert_topic(self, tid, title):
        sql = 'INSERT INTO topic(tid, title) VALUE (%s, %s)'
        self.execute(sql, (tid, title))

    def insert_follow_topic(self, uid, topic, contribution):
        sql = 'INSERT INTO follow_topic(uid, tid, contribution)' \
              'VALUE (%s, %s, %s)'
        self.execute(sql, (uid, topic, contribution))

    def insert_tag(self, qid, tid):
        sql = 'INSERT INTO tag(qid, tid) VALUES (%s, %s)'
        self.execute(sql, (qid, tid))


    def get_wait(self):
        sql = "SELECT * FROM wait LIMIT 0, 100"
        sql2 = "DELETE FROM wait WHERE uid = %s"
        try:
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            uids = ((t[0]) for t in res)
            self.cursor.executemany(sql2, uids)
            self.conn.commit()
            return res
        except Exception as e:
            self.conn.rollback()
            print(str(e))
            return []

    def get_usr(self):
        sql = "SELECT uid, utoken, url FROM usr " \
              "WHERE NOT EXISTS (SELECT * FROM pass WHERE pass.uid = usr.uid) LIMIT 0, 1000"
        try:
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            self.conn.commit()
            return res
        except Exception as e:
            self.conn.rollback()
            print(str(e))
            return []

    def get_answer_count(self, uid):
        sql = "SELECT answer_count FROM usr WHERE uid = %s"
        try:
            self.cursor.execute(sql, uid)
            res = self.cursor.fetchone()
            self.conn.commit()
            return res
        except Exception as e:
            self.conn.rollback()
            print(str(e))
            return 0

    def fetch_all(self, sql, args=None):
        try:
            self.execute(sql, args)
            res = self.cursor.fetchall()
            self.conn.commit()
            return res
        except Exception as e:
            self.conn.rollback()
            print(str(e))
            return None


    def fetch_one(self, sql, args=None):
        try:
            self.execute(sql, args)
            res = self.cursor.fetchone()
            self.conn.commit()
            return res
        except Exception as e:
            self.conn.rollback()
            print(str(e))
            return None
