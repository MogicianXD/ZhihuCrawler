"""
Settings for global.
"""
#####################################################################
# Scrapy settings of this project
#####################################################################
# scrapy basic info
BOT_NAME = 'haiproxy'
SPIDER_MODULES = ['crawler.spiders', 'crawler.validators']
NEWSPIDER_MODULE = 'crawler'

# downloader settings
ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
DOWNLOAD_TIMEOUT = 30
# to aviod infinite recursion
DEPTH_LIMIT = 100
CONCURRENT_REQUESTS = 50
# don't filter anything, also can set dont_filter=True in Request objects
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'
HTTPCACHE_ENABLED = False
GFW_PROXY = 'http://127.0.0.1:8123'

# splash settings.If you use docker-compose,SPLASH_URL = 'http://splash:8050'
SPLASH_URL = 'http://splash:8050'

# extension settings
RETRY_ENABLED = False
TELNETCONSOLE_ENABLED = False


DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.UserAgentMiddleware': 543,
    'crawler.middlewares.ProxyMiddleware': 543,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    # it should be before than HttpProxyMiddleware
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

# scrapy log settings
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'logs/haipproxy.log'


#####################################################################
# Custom settings of this project
#####################################################################
# redis settings.If you use docker-compose, REDIS_HOST = 'redis'
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_PASSWORD = '1037'
DEFAULT_REDIS_DB = 0
META_DATA_DB = 0

# scheduler settings
TIMER_RECORDER = 'haipproxy:schduler:task'
LOCKER_PREFIX = 'haipproxy:lock:'

# proxies crawler's settings
SPIDER_FEED_SIZE = 10
SPIDER_COMMON_TASK = 'haipproxy:spider:common'
SPIDER_AJAX_TASK = 'haipproxy:spider:ajax'
SPIDER_GFW_TASK = 'haipproxy:spider:gfw'
SPIDER_AJAX_GFW_TASK = 'haipproxy:spider:ajax_gfw'

# data_all is a set , it's a dupefilter
DATA_ALL = 'haipproxy:all'
# the data flow is init queue->validated_queue->validator_queue(temp)->validated_queue(score queue)->
# ttl_queue, speed_qeuue -> clients
# http_queue is a list, it's used to store initially http/https proxy resourecs
INIT_HTTP_QUEUE = 'haipproxy:init:http'
# socks proxy resources container
INIT_SOCKS4_QUEUE = 'haipproxy:init:socks4'
INIT_SOCKS5_QUEUE = 'haipproxy:init:socks5'

# custom validator settings
VALIDATOR_FEED_SIZE = 50

# they are temp sets, come from init queue, in order to filter transparnt ip
TEMP_HTTP_QUEUE = 'haipproxy:http:temp'
TEMP_HTTPS_QUEUE = 'haipproxy:https:temp'
TEMP_WEIBO_QUEUE = 'haipproxy:weibo:temp'
TEMP_ZHIHU_QUEUE = 'haipproxy:zhihu:temp'

# valited queues are zsets.squid and other clients fetch ip resources from them.
VALIDATED_HTTP_QUEUE = 'haipproxy:validated:http'
VALIDATED_HTTPS_QUEUE = 'haipproxy:validated:https'
VALIDATED_WEIBO_QUEUE = 'haipproxy:validated:weibo'
VALIDATED_ZHIHU_QUEUE = 'haipproxy:validated:zhihu'

# time to life of proxy ip resources
TTL_VALIDATED_RESOURCE = 2  # minutes
TTL_HTTP_QUEUE = 'haipproxy:ttl:http'
TTL_HTTPS_QUEUE = 'haipproxy:ttl:https'
TTL_WEIBO_QUEUE = 'haipproxy:ttl:weibo'
TTL_ZHIHU_QUEUE = 'haipproxy:ttl:zhihu'

# queue for proxy speed
SPEED_HTTP_QUEUE = 'haipproxy:speed:http'
SPEED_HTTPS_QUEUE = 'haipproxy:speed:https'
SPEED_WEIBO_QUEUE = 'haipproxy:speed:weibo'
SPEED_ZHIHU_QUEUE = 'haipproxy:speed:zhihu'

# squid settings on linux os
# execute sudo chown -R $USER /etc/squid/ and
# sudo chown -R $USER /var/log/squid/cache.log at first
SQUID_BIN_PATH = 'C:\Squid\\bin'  # mac os '/usr/local/sbin/squid'
SQUID_CONF_PATH = 'C:\Squid\etc\squid\squid.conf'  # mac os '/usr/local/etc/squid.conf'
SQUID_TEMPLATE_PATH = 'C:\Squid\etc\squid\squid.conf.default'  # mac os /usr/local/etc/squid.conf.backup

# client settings
# client picks proxies which's response time is between 0 and 5 seconds
LONGEST_RESPONSE_TIME = 10
# client picks proxies which's score is not less than 7
LOWEST_SCORE = 7
