'''
WeRead.py
Copyright 2020 by Algebra-FUN
ALL RIGHTS RESERVED.
'''

from matplotlib import pyplot as plt
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from .script import img2pdf, dir_check, os_start_file, clear_temp, escape

from time import sleep
import os
import requests
import time


class WeRead:
    """
        The agency who control `WeRead` web page with selenium webdriver to processing book scanning.

        `微信读书`网页代理，用于图书扫描

        :Args:
         - headless_driver:
                Webdriver instance with headless option set.
                设置了headless的Webdriver示例

        :Returns:
         - WeReadInstance

        :Usage:
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')

            headless_driver = Chrome(chrome_options=chrome_options)

            weread = WeRead(headless_driver)
    """

    def __init__(self, headless_driver: WebDriver, patience=30, debug=False):
        headless_driver.get('https://weread.qq.com/')
        headless_driver.implicitly_wait(5)
        self.driver: WebDriver = headless_driver
        self.patience = patience
        self.debug_mode = debug

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if not self.debug_mode:
            clear_temp('wrs-temp')

    def S(self, selector):
        return WebDriverWait(self.driver, self.patience).until(lambda driver: driver.find_element(By.CSS_SELECTOR, selector))

    def click(self, target):
        self.driver.execute_script('arguments[0].click();', target)

    def shot_full_canvas_context(self, file_name):
        renderTargetContainer = self.S('.renderTargetContainer')
        height = renderTargetContainer.get_property('offsetHeight')
        height += renderTargetContainer.get_property('offsetTop')
        width = self.driver.execute_script("return window.outerWidth")
        self.driver.set_window_size(width, height)
        sleep(1)
        content = self.S('.app_content')
        content.screenshot(file_name)

    def check_all_image_loaded(self, frequency=10, max_wait_duration=30):
        """
        check if all image is loaded.

        检查图书Image是否全部加载完毕.
        """
        interval = 1/frequency

        try:
            img_unloaded = WebDriverWait(self.driver, 3).until(
                lambda driver: driver.find_elements(By.CSS_SELECTOR, 'img.wr_absolute'))
        except Exception:
            return False

        for _ in range(frequency*max_wait_duration):
            sleep(interval)
            for img in img_unloaded:
                if img.get_property('complete'):
                    img_unloaded.remove(img)
            if not len(img_unloaded):
                self.debug_mode and print('all image is loaded!')
                return True
        return False

    def login(self):
        """登录微信读书"""
        print("开始登录流程...")
        
        # 确保我们在主页上
        if not self.driver.current_url.endswith("weread.qq.com/"):
            print("重定向到主页...")
            self.driver.get("https://weread.qq.com/")
            time.sleep(2)
        
        print("等待页面加载...")
        print(f"页面标题: {self.driver.title}")
        print(f"当前URL: {self.driver.current_url}")
        
        # 等待页面完全加载
        time.sleep(5)
        
        print("正在查找登录按钮...")
        login_button = None
        
        # 尝试多个选择器来查找登录按钮
        selectors = [
            (By.XPATH, "//a[text()='登录']"),
            (By.XPATH, "//a[contains(text(), '登录')]"),
            (By.CSS_SELECTOR, "a[href*='login']"),
            (By.CSS_SELECTOR, ".login_button"),
            (By.CSS_SELECTOR, "[class*='login']"),
            (By.CSS_SELECTOR, "a.navBar_link"),
            (By.CSS_SELECTOR, ".navBar_link"),
            (By.CSS_SELECTOR, ".wr_btn_item"),
            (By.CSS_SELECTOR, ".navBar_item")
        ]
        
        for by, selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector)
                print(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                for element in elements:
                    print(f"元素文本: {element.text}")
                    print(f"元素HTML: {element.get_attribute('outerHTML')}")
                    if element.is_displayed() and ('登录' in element.text or 'login' in element.get_attribute('outerHTML').lower()):
                        login_button = element
                        break
                if login_button:
                    break
            except Exception as e:
                print(f"选择器 {selector} 失败: {e}")
                continue
        
        if login_button:
            try:
                print("找到登录按钮，准备点击")
                # 尝试滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(1)
                
                # 尝试移动到按钮位置
                actions = ActionChains(self.driver)
                actions.move_to_element(login_button).perform()
                time.sleep(1)
                
                # 尝试点击
                login_button.click()
                print("已点击登录按钮")
                
                # 等待一下让页面响应
                time.sleep(3)
                
            except Exception as e:
                print(f"点击登录按钮失败: {e}")
                try:
                    print("尝试使用JavaScript点击")
                    self.driver.execute_script("arguments[0].click();", login_button)
                    print("JavaScript点击成功")
                    time.sleep(3)
                except Exception as e:
                    print(f"JavaScript点击也失败了: {e}")
                    raise Exception("无法点击登录按钮")
        else:
            print("尝试使用JavaScript查找和点击登录按钮...")
            try:
                # 尝试多个JavaScript选择器
                js_selectors = [
                    "document.querySelector('a[href*=\"login\"]')",
                    "document.querySelector('.login_button')",
                    "document.querySelector('[class*=\"login\"]')",
                    "Array.from(document.querySelectorAll('a')).find(a => a.textContent.includes('登录'))",
                    "document.querySelector('.navBar_link')",
                    "document.querySelector('.wr_btn_item')",
                    "document.querySelector('.navBar_item')"
                ]
                
                for selector in js_selectors:
                    print(f"尝试JavaScript选择器: {selector}")
                    result = self.driver.execute_script(f"return {selector}")
                    if result:
                        print(f"找到元素: {self.driver.execute_script(f'return {selector}.outerHTML')}")
                        self.driver.execute_script(f"{selector}.click()")
                        print("JavaScript点击成功")
                        time.sleep(3)
                        break
                else:
                    raise Exception("无法找到登录按钮")
            except Exception as e:
                print(f"JavaScript操作失败: {e}")
                raise Exception("无法找到或点击登录按钮")
        
        print("正在等待二维码出现...")
        try:
            # 等待登录对话框出现
            dialog_selectors = [
                '.login_dialog',
                '.login_container',
                '.login_qrcode_wrapper',
                '.login_qrcode',
                '[class*="login"]'
            ]
            
            dialog = None
            max_attempts = 30  # 最多等待30秒
            for attempt in range(max_attempts):
                print(f"尝试查找登录对话框，第 {attempt + 1} 次...")
                for selector in dialog_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                        for element in elements:
                            if element.is_displayed():
                                print(f"找到可见的对话框元素: {element.get_attribute('outerHTML')}")
                                dialog = element
                                break
                        if dialog:
                            break
                    except:
                        continue
                if dialog:
                    break
                time.sleep(1)
            
            if not dialog:
                print("无法找到登录对话框，尝试截取整个页面...")
                if not os.path.exists('wrs-temp'):
                    os.makedirs('wrs-temp')
                self.driver.save_screenshot('wrs-temp/login_page.png')
                print("已保存页面截图到 wrs-temp/login_page.png")
                raise Exception("无法找到登录对话框")
            
            # 给二维码加载一些时间
            time.sleep(3)
            
            # 尝试多个选择器来查找二维码
            qrcode_selectors = [
                '.login_dialog_qrcode img',
                '.login_qrcode img',
                'img[class*="qrcode"]',
                '.login_dialog img',
                '.login_qrcode_wrapper img',
                '.login_container img',
                'img[src*="qrcode"]'
            ]
            
            qrcode = None
            for selector in qrcode_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"使用选择器 {selector} 找到 {len(elements)} 个元素")
                    for element in elements:
                        print(f"元素HTML: {element.get_attribute('outerHTML')}")
                        if element.is_displayed():
                            qrcode = element
                            break
                    if qrcode:
                        break
                except:
                    continue
            
            if not qrcode:
                print("未找到二维码，尝试截取整个登录对话框...")
                if not os.path.exists('wrs-temp'):
                    os.makedirs('wrs-temp')
                dialog.screenshot('wrs-temp/login_qrcode.png')
                print("已保存登录对话框截图到 wrs-temp/login_qrcode.png")
                return
            
            # 获取二维码图片URL
            qrcode_url = qrcode.get_attribute('src')
            print(f"找到二维码图片: {qrcode_url}")
            
            # 下载二维码图片
            if not os.path.exists('wrs-temp'):
                os.makedirs('wrs-temp')
            
            response = requests.get(qrcode_url)
            with open('wrs-temp/login_qrcode.png', 'wb') as f:
                f.write(response.content)
            print("二维码已保存到 wrs-temp/login_qrcode.png")
            
            # 等待用户扫码
            print("请使用微信扫描二维码登录...")
            WebDriverWait(self.driver, 300).until(
                lambda x: 'login' not in x.current_url
            )
            print("登录成功！")
            
        except Exception as e:
            print(f"查找二维码时出错: {e}")
            print("页面源码：")
            print(self.driver.page_source)
            raise Exception("无法找到二维码")

    def switch_to_context(self):
        """switch to main body of the book"""
        self.S('button.catalog').click()
        self.S('li.chapterItem:nth-child(2)').click()

    def set_font_size(self, font_size_index=1):
        """
        set font size

        设置字体大小

        :Args:
         - font_size_index=0:
                the index of font size(1-7)
                字体大小级别(1-7)
                In particular, 1 represents minimize, 7 represents maximize
                特别地，1为最小，7为最大
        """
        sleep(1)
        self.S('button.fontSizeButton').click()
        sleep(1)
        self.S(f'.vue-slider-mark:nth-child({font_size_index})').click()
        self.S('.app_content').click()

    def turn_light_on(self):
        sleep(1)
        self.S('button.readerControls_item.white').click()

    def scan2pdf(self, book_url, save_at='.', binary_threshold=200, quality=100, show_output=True, font_size_index=1):
        """
        scan `weread` book to pdf and save offline.

        扫面`微信读书`的书籍转换为PDF并保存本地

        :Args:
         - book_url:
                the url of weread book which aimed to scan
                扫描目标书籍的ULR
         - save_at='.':
                the path of where to save
                保存地址
         - binary_threshold=200:
                threshold of scan binary
                二值化处理的阈值
         - quality=95:
                quality of scan pdf
                扫描PDF的质量
         - show_output=True:
                if show the output pdf file at the end of this method
                是否在该方法函数结束时展示生成的PDF文件
         - font_size_index=1:
                the index of font size(1-7)
                字体大小级别(1-7)
                In particular, 1 represents minimize, 7 represents maximize
                特别地，1为最小，7为最大

        :Usage:
            weread.scan2pdf('https://weread.qq.com/web/reader/a57325c05c8ed3a57224187kc81322c012c81e728d9d180')
        """
        print('Task launching...')

        # valid the url
        if 'https://weread.qq.com/web/reader/' not in book_url:
            raise Exception('WeRead.UrlError: Wrong url format.')

        # switch to target book url
        self.driver.get(book_url)
        print(f'navigate to {book_url}')

        # turn theme to light theme
        self.turn_light_on()

        # set font size
        self.set_font_size(font_size_index)

        # switch to target book's cover
        self.switch_to_context()

        # get the name of the book
        book_name = escape(self.S('span.readerTopBar_title_link').text)
        print(f'preparing to scan "{book_name}"')

        # check the dir for future save
        dir_check(f'wrs-temp/{book_name}/context')

        # used to store png_name for pdf converting
        png_name_list = []

        page = 1

        while True:
            sleep(1)

            # get chapter
            chapter = escape(self.S('span.readerTopBar_title_chapter').text)
            print(f'scanning chapter "{chapter}"')

            # locate the renderTargetContent
            context = self.S('div.app_content')

            # check all image loaded
            self.check_all_image_loaded()

            # context_scan2png
            png_name = f'wrs-temp/{book_name}/context/{chapter}_{page}'
            self.shot_full_canvas_context(f'{png_name}.png')

            png_name_list.append(png_name)
            print(f'save chapter scan {png_name}')

            # find next page or chapter button
            try:
                readerFooter = self.S(
                    '.readerFooter_button,.readerFooter_ending')
            except Exception:
                break

            readerFooterClass = readerFooter.get_attribute('class')

            # quick ending
            if 'ending' in readerFooterClass:
                break

            next_btn_text = readerFooter.text.strip()

            if next_btn_text == "下一页":
                print("go to next page")
                page += 1
            elif next_btn_text == "下一章":
                print("go to next chapter")
                page = 1
            else:
                raise Exception("Unexpected Exception")

            # go to next page or chapter
            readerFooter.click()

        print('pdf converting...')

        # convert to pdf and save offline
        img2pdf(f'{save_at}/{book_name}', png_name_list,
                binary_threshold=binary_threshold, quality=quality)
        print('scanning finished.')
        if show_output:
            os_start_file(f'{save_at}/{book_name}.pdf')
