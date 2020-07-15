# coding: utf-8

import requests
import time
import json
import os
import sys
from bs4 import BeautifulSoup as BS
import urllib.parse
import webbrowser

from io import BytesIO
from zhihu_captcha import utils
from zhihu_captcha import orcmodel
import tensorflow as tf
from PIL import Image
import numpy as np

try:
    type (eval('model'))
except:
    model = orcmodel.LSTMOCR('infer')
    model.build_graph()

config = tf.ConfigProto(allow_soft_placement=True)
checkpoint_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoint")


class ZhihuCaptcha():

    def __init__(self, username=None, password=None):
        if sys.path[0]: os.chdir(sys.path[0])  # 设置脚本所在目录为当前工作目录

        # 恢复权重
        self.__sess = self.__restoreSess(checkpoint_dir)

    # 恢复权重
    def __restoreSess(self, checkpoint=checkpoint_dir):
        sess=tf.Session(config=config)
        sess.run(tf.global_variables_initializer())
        saver = tf.train.Saver(tf.global_variables(), max_to_keep=100)
        ckpt = tf.train.latest_checkpoint(checkpoint)
        if ckpt:
            #回复权限，这里连 global_step 也会被加载进来
            saver.restore(sess, ckpt)
            # print('restore from the checkpoint{0}'.format(ckpt))
            print('已加载checkpoint{0}'.format(ckpt))
        else:
            print('警告：未加载任何chechpoint')
            print('如果这不是你预期中的，请确保以下目录存在可用的checkpoint:\n{0}'.format(checkpoint_dir))
        return sess


    def recgImg(self, img):
        """
        可以在线测试验证码识别功能
        参数：
            img 一个 (60, 150) 的图片
        """
        im = np.array(img.convert("L")).astype(np.float32)/255.
        im = np.reshape(im, [60, 150, 1])
        inp=np.array([im])
        seq_len_input=np.array([np.array([64 for _ in inp], dtype=np.int64)])
        #seq_len_input = np.asarray(seq_len_input)
        seq_len_input = np.reshape(seq_len_input, [-1])
        imgs_input = np.asarray([im])
        feed = {model.inputs: imgs_input,model.seq_len: seq_len_input}
        dense_decoded_code = self.__sess.run(model.dense_decoded, feed)
        expression = ''
        for i in dense_decoded_code[0]:
            if i == -1:
                expression += ''
            else:
                expression += utils.decode_maps[i]
        return expression
