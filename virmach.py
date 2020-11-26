# 当前存在的问题：
# 1.下单流程不完善，
# 2.配置信息不确定，需要更新配置中的key

import requests
import sys
from time import sleep
import json
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from retrying import retry
import multiprocessing

HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36",
    'Referer': "https://billing.virmach.com",
    'Host': 'billing.virmach.com'
}
contents = []
last = ''
url = 'https://billing.virmach.com/modules/addons/blackfriday/new_plan.json'

vars_now = vars()

if sys.platform in ('win32', 'win64'):
    from winsound import Beep


    def BEEP():
        Beep(500, 300)
        sleep(0.100)
        Beep(500, 300)
        sleep(0.100)
        Beep(500, 300)
else:
    def BEEP():
        pass


def wait_new_machine():
    while True:
        req = requests.get(url, headers=HEADERS)
        c = req.content.decode('utf-8')
        if c != '':
            j = json.loads(c)
            if j not in contents and j is not last:
                BEEP()
                contents.append(j)
                return j
        sleep(0.5)
        print('\rsleep', end='')


class VirmachSelenium(object):

    def __init__(self, email, password, configures, ones=True):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        # self.bro = webdriver.Chrome(chrome_options=chrome_options)
        self.bro = webdriver.Chrome()
        self.login(email, password)
        self.configures = configures
        self.ones = ones

    @retry(stop_max_attempt_number=3, retry_on_result=lambda x: False if x else True)
    def login(self, email, password):
        """登录，成功返回1，不成功返回0并重试3次后报错"""
        url = 'https://billing.virmach.com/index.php?rp=/login'
        self.bro.get(url)
        xpath_email = '//*[@id="inputEmail"]'
        xpath_password = '//*[@id="inputPassword"]'
        self.bro.find_element_by_xpath(xpath_email).send_keys(email)
        self.bro.find_element_by_xpath(xpath_password).send_keys(password)
        xpath_login = '//*[@id="login"]'
        self.bro.find_element_by_xpath(xpath_login).click()
        try:
            self.bro.find_element_by_xpath(xpath_email)
            return False
        except selenium.common.exceptions.NoSuchElementException:
            return True

    def step_review(self):
        xpath_checkout = '//*[@id="checkout"]'
        self.bro.find_element_by_xpath(xpath_checkout).click()

    def step_checkout(self):
        xpath_Alipay = '//*[@id="paymentGatewaysContainer"]/div/label/label/label/div/div[2]'
        self.bro.find_element_by_xpath(xpath_Alipay).click()
        alert = self.bro.switch_to.alert()
        alert.accept()

        xpath_agree_service = '//*[@id="iCheck-accepttos"]/ins'
        self.bro.find_element_by_xpath(xpath_agree_service).click()

        xpath_complete_order = '//*[@id="btnCompleteOrder"]'
        self.bro.find_element_by_xpath(xpath_complete_order).click()

    def filter_machine(self, j):
        # configures_example = [
        #     {
        #         'price': 5,  # less then
        #         'memory': 1024,  # more then x MB
        #         'CPU': 2,  # more then
        #         'disk': 5,  # more then x GB
        #         'bandwidth': 1000,  # more then x GB
        #         'ip': 1,  # more then
        #         'win': True,  # 如果值为true，则只选则win主机
        #         'location': ['Buffalo', 'Los Angeles', 'Atlanta', 'Dallas', 'Chicago', 'Seatttle', 'Frankfurt',
        #                      'Phoenix',
        #                      'Piscataway', 'San Jose', 'Amsterdam']  # 需要哪个机房写哪个，不可置空
        #     },  # 这是第一个预设，可以同时存在多个预设方案
        # ]
        for configure in self.configures:
            price = configure.pop('price')
            location = configure.pop('location')
            if j['location'] not in location:
                continue
            if j['price'] > price:
                continue
            for key, value in configure.items():
                v = j.get(key, 0)
                if value < v:
                    continue
            return True

    def flush_login(self):
        xpath_logout = '//*[@id="top-nav"]/ul/li[3]/a'
        try:
            self.bro.find_element_by_xpath(xpath_logout)
            self.bro.get('https://billing.virmach.com/index.php')
        except selenium.common.exceptions.NoSuchElementException:
            self.login()

    def run(self, q):
        first = True
        while not self.ones or first:
            try:
                j = q.get(timeout=60)
            except UnboundLocalError:
                self.flush_login()
                continue
            if self.filter_machine(j) is False:
                continue
            self.step_review()
            self.step_checkout()


def account_1():
    configures = [
        {
            'price': 5,  # less then
            'memory': 1024,  # more then x MB
            'CPU': 2,  # more then
            'disk': 5,  # more then x GB
            'bandwidth': 1000,  # more then x GB
            'ip': 1,  # more then
            'win': True,  # 如果值为true，则只选则win主机
            'location': ['Buffalo', 'Los Angeles', 'Atlanta', 'Dallas', 'Chicago', 'Seatttle', 'Frankfurt', 'Phoenix',
                         'Piscataway', 'San Jose', 'Amsterdam']  # 需要哪个机房写哪个，不可置空
        },  # 这是第一个预设，可以同时存在多个预设方案
    ]
    func = VirmachSelenium(email='virmach@ruri.live',
                           password='1995Xiaobai.123=',
                           configures=configures,
                           ones=True)
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=func.run, args=(q,))
    return p, q


def run():
    process_list = []
    # 初始化预设账户
    for account, configure in vars_now.items():
        if account.startswith('account_'):
            print('添加账户: %s' % account)
            process_list.append(configure())
    # 每个账户启动一个进程
    for p, q in process_list:
        p.start()
    # 刷新新机器数据，刷新到则向每个账户进程推送配置信息
    j = wait_new_machine()
    for p, q in process_list:
        q.put(j)
    # 正常退出，暂时还没写，应该不会执行到这
    for p, q in process_list:
        p.join()


if __name__ == '__main__':
    run()
