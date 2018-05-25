# -*- coding: utf-8 -*-
import random
import time, sys
import json
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

class CNBlogSelenium(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

        opt = webdriver.ChromeOptions()
        # 设置无头模式，调试的时候可以注释这句
        # opt.set_headless()
        self.driver = webdriver.Chrome(executable_path=r"/usr1/webdrivers/chromedriver", chrome_options=opt)
        self.driver.set_window_size(1440, 900)

    def visit_login(self):
        bRet = False
        try:
            self.driver.get("https://passport.cnblogs.com/user/signin")

            WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="input1"]')))
            username = self.driver.find_element_by_xpath('//*[@id="input1"]')
            username.clear()
            username.send_keys(self.username)

            WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="input2"]')))
            password = self.driver.find_element_by_xpath('//*[@id="input2"]')
            password.clear()
            password.send_keys(self.password)

            WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signin"]')))
            signin = self.driver.find_element_by_xpath('//*[@id="signin"]')
            signin.click()

            WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="geetest_radar_tip_content"]')))
            geetest = self.driver.find_element_by_xpath('//*[@class="geetest_radar_tip_content"]')
            geetest.click()

            #点击滑动验证码后加载图片需要时间
            time.sleep(3)

            bRet = self.analog_move()

            # 保存cookies到本地
            self.save_cookies()
        except :
            pass

        self.driver.quit()
        return bRet

    def analog_move(self):
        WebDriverWait(self.driver, 10, 0.5).until(EC.element_to_be_clickable(
            (By.XPATH, '//canvas[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')))
        element = self.driver.find_element_by_xpath(
            '//canvas[@class="geetest_canvas_fullbg geetest_fade geetest_absolute"]')

        self.driver.get_screenshot_as_file("login.png")
        image = Image.open("login.png")
        left = element.location.get("x")
        top = element.location.get("y")
        right = left + element.size.get("width")
        bottom = top + element.size.get("height")
        cropImg = image.crop((left, top, right, bottom))
        full_Img = cropImg.convert("L")
        full_Img.save("fullimage.png")

        WebDriverWait(self.driver, 10, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="geetest_slider_button"]')))
        move_btn = self.driver.find_element_by_xpath('//*[@class="geetest_slider_button"]')

        ActionChains(self.driver).move_to_element(move_btn).click_and_hold(move_btn).perform()

        WebDriverWait(self.driver, 10, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, '//canvas[@class="geetest_canvas_slice geetest_absolute"]')))
        element = self.driver.find_element_by_xpath('//canvas[@class="geetest_canvas_slice geetest_absolute"]')

        self.driver.get_screenshot_as_file("login.png")
        image = Image.open("login.png")
        left = element.location.get("x")
        top = element.location.get("y")
        right = left + element.size.get("width")
        bottom = top + element.size.get("height")
        cropImg = image.crop((left, top, right, bottom))
        cut_Img = cropImg.convert("L")
        cut_Img.save("cutimage.png")

        distance, span = self.calc_cut_offset(cut_Img, full_Img)
        print(distance, span)
        self.start_move(distance, move_btn, False)

        time.sleep(2)

        tip_btn = self.driver.find_element_by_xpath('//*[@id="tip_btn"]')
        try:
            if tip_btn.text.find("登录成功") == -1:
                try:
                    WebDriverWait(self.driver, 3, 0.5).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="geetest_reset_tip_content"]')))
                    reset_btn = self.driver.find_element_by_xpath('//*[@class="geetest_reset_tip_content"]')
                    if reset_btn.text.find("重试") != -1:
                        reset_btn.click()
                except:
                    pass
                else:
                    time.sleep(1)
                refresh_btn = self.driver.find_element_by_xpath('//*[@class="geetest_refresh_1"]')
                refresh_btn.click()
                time.sleep(0.5)
                return self.analog_move()
        except:
            #登录成功后会切换到主页，所以获取不到tip_btn按钮
            print("登录成功")
            return True
        return False

    def calc_cut_offset(self, cut_img, full_img):
        x, y = 1, 1
        find_one = False
        top = 0
        left = 0
        right = 0
        while x < cut_img.width:
            y = 1
            while y < cut_img.height:
                cpx = cut_img.getpixel((x, y))
                fpx = full_img.getpixel((x, y))
                if abs(cpx - fpx) > 50:
                    if not find_one:
                        find_one = True
                        x += 60
                        y -= 10
                        continue
                    else:
                        if left == 0:
                            left = x
                            top = y
                        right = x
                        break
                y += 1
            x += 1

        img = cut_img.crop((left, top, right, top + 60))
        img.save("new_cut.png")
        return left, right - left

    # 开始移动
    def start_move(self, distance, element, click_hold=False):
        # element = self.driver.find_element_by_xpath('//div[@class="gt_slider_knob gt_show"]')

        # 这里就是根据移动进行调试，计算出来的位置不是百分百正确的，加上一点偏移
        # distance -= element.size.get('width') / 2
        distance -= 7
        print(distance)

        # 按下鼠标左键
        if click_hold:
            ActionChains(self.driver).click_and_hold(element).perform()
        # time.sleep(0.5)
        while distance > 0:
            if distance > 10:
                # 如果距离大于10，就让他移动快一点
                span = random.randint(5, 8)
            else:
                time.sleep(random.randint(10, 50) / 100)
                # 快到缺口了，就移动慢一点
                span = random.randint(2, 3)
            ActionChains(self.driver).move_by_offset(span, 0).perform()
            distance -= span

        ActionChains(self.driver).move_by_offset(distance, 1).perform()
        ActionChains(self.driver).release(on_element=element).perform()

    # 保存cookies
    def save_cookies(self):
        cookies = self.driver.get_cookies()
        with open("cookies.txt", "w") as fp:
            json.dump(cookies, fp)

def analog_login(username, password):
    c = CNBlogSelenium(username, password)
    return c.visit_login()

if __name__ == "__main__":
    c = CNBlogSelenium("用户名", "密码")
    c.visit_login()

    
