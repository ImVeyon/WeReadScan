"""
demo.py
The demo of WeReadScan.py
Copyright 2020 by Algebra-FUN
ALL RIGHTS RESERVED.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver import Edge
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

from WeReadScan import WeRead

# options
options = Options()
# options.add_argument('--headless')  #! important argument
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument('disable-infobars')
options.add_argument('log-level=3')

# launch Webdriver
print('Webdriver launching...')
service = Service()
driver = Edge(service=service, options=options)
print('Webdriver launched.')

# 先访问微信读书主页
print('访问微信读书主页...')
driver.get('https://weread.qq.com/')
print('页面加载完成')

with WeRead(driver,debug=True) as weread:
    print('开始登录流程...')
    weread.login() #? login for grab the whole book
    print('登录成功，开始扫描图书...')
    weread.scan2html('https://weread.qq.com/web/reader/f83320a0813ab9c90g015c2e')