# -- coding: utf-8 --
"""
Copyright (c) 2024 [Hosea]
Licensed under the MIT License.
See LICENSE file in the project root for full license information.
"""
import os
import time
import traceback
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import dashscope
from dashscope import Generation

# 设置 DashScope API Key（请替换为你的实际 API Key）
dashscope.api_key = os.environ.get("DASHSCOPE_API_KEY", "YOUR_API_KEY_HERE")

ns_random = os.environ.get("NS_RANDOM","false")
cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
headless = os.environ.get("HEADLESS", "true").lower() == "true"

def call_qwen(title, content):
    """调用 Qwen API 生成一句话评论"""
    prompt = f"""
你是一个活跃在技术论坛上的用户。
请你根据以下帖子标题和内容，生成一句简洁得体的回帖评论：
要求：语气自然、友好、不超过20字。

【标题】{title}
【内容】{content[:100]}  # 控制长度避免超限
"""

    try:
        response = Generation.call(
            model="qwen-plus",  # 可选：qwen-max / qwen-plus / qwen-turbo
            prompt=prompt
        )
        reply = response.output.text.strip()
        return reply
    except Exception as e:
        print(f"[AI回复失败] 错误信息：{e}")
        return "已阅读，支持一下！"

def fetch_title_and_content(driver):
    """从当前页面提取帖子标题和一楼内容"""
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    title_tag = soup.find('a', class_='post-title-link')
    title = title_tag.text.strip() if title_tag else "无标题"

    # 提取一楼内容
    content_tag = soup.find('article', class_='post-content')
    content = content_tag.get_text(strip=True) if content_tag else "无内容"

    return title, content

def click_sign_icon(driver):
    """
    尝试点击签到图标和试试手气按钮的通用方法
    """
    try:
        print("开始查找签到图标...")
        sign_icon = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//span[@title='签到']"))
        )
        print("找到签到图标，准备点击...")

        driver.execute_script("arguments[0].scrollIntoView(true);", sign_icon)
        time.sleep(0.5)

        try:
            sign_icon.click()
        except:
            driver.execute_script("arguments[0].click();", sign_icon)

        print("签到图标点击成功")
        time.sleep(5)
        print(f"当前页面URL: {driver.current_url}")

        try:
            click_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '试试手气')]"))
            ) if ns_random else WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '鸡腿 x 5')]"))
            )
            click_button.click()
            print("完成试试手气点击")
        except Exception as lucky_error:
            print(f"试试手气按钮点击失败或者签到过了: {str(lucky_error)}")

        return True

    except Exception as e:
        print(f"签到过程中出错: {str(e)}")
        print(f"当前页面URL: {driver.current_url}")
        print(traceback.format_exc())
        return False

def setup_driver_and_cookies():
    """
    初始化浏览器并设置cookie的通用方法
    返回: 设置好cookie的driver实例
    """
    try:
        cookie = os.environ.get("NS_COOKIE") or os.environ.get("COOKIE")
        headless = os.environ.get("HEADLESS", "true").lower() == "true"

        if not cookie:
            print("未找到cookie配置")
            return None

        print("开始初始化浏览器...")
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        print("正在启动Chrome...")
        driver = uc.Chrome(options=options)

        if headless:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_window_size(1920, 1080)

        print("Chrome启动成功")

        print("正在设置cookie...")
        driver.get('https://www.nodeseek.com')
        time.sleep(5)

        for cookie_item in cookie.split(';'):
            try:
                name, value = cookie_item.strip().split('=', 1)
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.nodeseek.com',
                    'path': '/'
                })
            except Exception as e:
                print(f"设置cookie出错: {str(e)}")
                continue

        print("刷新页面...")
        driver.refresh()
        time.sleep(5)
        return driver

    except Exception as e:
        print(f"设置浏览器和Cookie时出错: {str(e)}")
        print(traceback.format_exc())
        return None

def nodeseek_comment(driver):
    try:
        print("正在访问交易区...")
        target_url = 'https://www.nodeseek.com/categories/trade'
        driver.get(target_url)
        print("等待页面加载...")

        posts = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.post-list-item'))
        )
        print(f"成功获取到 {len(posts)} 个帖子")

        valid_posts = [post for post in posts if not post.find_elements(By.CSS_SELECTOR, '.pined')]
        selected_posts = random.sample(valid_posts, min(20, len(valid_posts)))

        for i, post in enumerate(selected_posts):
            try:
                post_link = post.find_element(By.CSS_SELECTOR, '.post-title a')
                post_url = post_link.get_attribute('href')
                print(f"正在处理第 {i+1} 个帖子: {post_url}")
                
                driver.get(post_url)

                # 获取帖子标题和内容
                title, content = fetch_title_and_content(driver)

                # 使用 AI 生成一句话回复
                ai_reply = call_qwen(title, content)
                print(f"AI生成回复: {ai_reply}")

                # 等待 CodeMirror 编辑器加载
                editor = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.CodeMirror'))
                )
                editor.click()
                time.sleep(0.5)

                # 输入 AI 回复
                actions = ActionChains(driver)
                for char in ai_reply:
                    actions.send_keys(char)
                    actions.pause(random.uniform(0.1, 0.3))
                actions.perform()

                # 提交评论
                submit_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'submit') and contains(@class, 'btn') and contains(text(), '发布评论')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(0.5)
                submit_button.click()

                print(f"已在帖子 {post_url} 中完成评论")
                time.sleep(random.uniform(2,5))

            except Exception as e:
                print(f"处理帖子时出错: {str(e)}")
                continue

        print("NodeSeek评论任务完成")

    except Exception as e:
        print(f"NodeSeek评论出错: {str(e)}")
        print(traceback.format_exc())

def click_chicken_leg(driver):
    try:
        print("尝试点击加鸡腿按钮...")
        chicken_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="nsk-post"]//div[@title="加鸡腿"][1]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chicken_btn)
        time.sleep(0.5)
        chicken_btn.click()
        print("加鸡腿按钮点击成功")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-confirm'))
        )

        try:
            error_title = driver.find_element(By.XPATH, "//h3[contains(text(), '该评论创建于7天前')]")
            if error_title:
                print("该帖子超过7天，无法加鸡腿")
                ok_btn = driver.find_element(By.CSS_SELECTOR, '.msc-confirm .msc-ok')
                ok_btn.click()
                return False
        except:
            ok_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.msc-confirm .msc-ok'))
            )
            ok_btn.click()
            print("确认加鸡腿成功")

        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.msc-overlay'))
        )
        time.sleep(1)
        return True

    except Exception as e:
        print(f"加鸡腿操作失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始执行NodeSeek评论脚本...")
    driver = setup_driver_and_cookies()
    if not driver:
        print("浏览器初始化失败")
        exit(1)
    nodeseek_comment(driver)
    click_sign_icon(driver)
    print("脚本执行完成")
