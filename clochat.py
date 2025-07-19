# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-07-11 14:06:56
# CloChat签到脚本
# -------------------------------
"""
CloChat签到
变量为账号密码
export CLOCHAT_USERNAME="账号"
export CLOCHAT_PASSWORD="密码"

cron: 10 10 * * *
const $ = new Env("clochat签到");
"""
import os
import time
import traceback
import logging
from notify import send
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 配置信息
USERNAME = os.environ.get("CLOCHAT_USERNAME")
PASSWORD = os.environ.get("CLOCHAT_PASSWORD")
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
LOG_LEVEL = os.environ.get("CLOCHAT_LOG_LEVEL", "DEBUG").upper()  # 日志级别

# 初始化日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)
# 设置日志输出等级
log.setLevel(logging.INFO if LOG_LEVEL == "INFO" else logging.DEBUG)

def setup_driver():
    """初始化浏览器"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    if HEADLESS:
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=options)

    if HEADLESS:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(1920, 1080)

    return driver

def login(driver):
    """使用账号密码登录"""
    if not USERNAME or not PASSWORD:
        log.error("未找到CLOCHAT_USERNAME或CLOCHAT_PASSWORD环境变量")
        return False

    log.debug("跳转至登录页面...")
    driver.get('https://clochat.com/login')

    try:
        # 输入用户名
        username_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "login-account-name"))
        )
        username_input.send_keys(USERNAME)

        # 输入密码
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "login-account-password"))
        )
        password_input.send_keys(PASSWORD)

        # 点击登录按钮
        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        login_button.click()

        # 等待登录完成（URL变化）
        WebDriverWait(driver, 30).until_not(
            EC.url_contains("login")
        )

        log.info("登录成功！")

        return True

    except Exception as e:
        log.error(f"登录过程中出错: {str(e)}")
        log.debug(f"当前页面源码片段: {driver.page_source[:1000]}...")
        return False

def send_sign_in_message_in_chat(driver):
    """在指定聊天室发送签到消息并检查结果"""
    CHAT_URL = "https://clochat.com/chat/c/-/2"

    try:
        log.debug(f"跳转至聊天室: {CHAT_URL}")
        driver.get(CHAT_URL)
        time.sleep(5)

        log.debug("等待输入框加载...")
        input_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "channel-composer"))
        )

        log.debug("清空输入框...")
        input_box.clear()

        log.debug("输入'签到'")
        input_box.send_keys("签到")

        log.debug("等待发送按钮可用...")
        send_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".chat-composer-button.-send"))
        )

        log.debug("点击发送按钮...")
        send_button.click()
        log.info("✅ 签到消息已发送！")

        # 检查是否有机器人回复
        time.sleep(5)
        messages = driver.find_elements(By.CSS_SELECTOR, ".chat-message-container.is-bot,.chat-message-container.is-current-user")
        if messages:
            last_message = messages[-1]
            chat_content = last_message.find_element(By.CSS_SELECTOR, ".chat-cooked p").text.strip()

            log.info(f"🔍 签到结果: {chat_content}")
            send(title="CLOCHAT 签到通知", content=chat_content)
        else:
            log.error("❌ 未检测到任何消息，请检查网络或页面是否加载完成。")

    except Exception as e:
        log.error(f"聊天室签到失败: {e}")
        log.debug(traceback.format_exc())
        #driver.save_screenshot(f"/ql/data/photo/chat_error_{int(time.time())}.png")

if __name__ == "__main__":
    driver = None
    try:
        log.info("开始执行CloChat签到脚本...")
        driver = setup_driver()

        if login(driver):
            log.debug("开始执行聊天室签到流程...")
            send_sign_in_message_in_chat(driver)
        else:
            log.debug("登录失败，无法继续签到。")

    finally:
        if driver:
            log.info("关闭浏览器...")
            driver.quit()
        log.info("脚本执行完成")
