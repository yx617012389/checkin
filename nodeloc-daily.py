# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz https://github.com/wh1te3zzz/checkin
# @Time : 2025-07-16 15:06:56
# NodeLoc任务脚本
# -------------------------------
"""
NodeLoc任务，已实现浏览话题、点赞
自行网页捉包提取请求头中的cookie和x-csrf-token填到变量 NLCookie 中,用#号拼接，多账号换行隔开
export NLCookie="_t=******; _forum_session=xxxxxx#XXXXXX"

cron: 40 8-23 * * *
const $ = new Env("NodeLoc任务");
"""
import os
import re
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import undetected_chromedriver as uc

# -------------------------------
# 用户配置项
# -------------------------------
MAX_TOPICS = int(os.environ.get("NL_MAX_TOPICS", "20"))  # 控制访问的帖子数量
MIN_DELAY = float(os.environ.get("NL_MIN_DELAY", "3"))     # 手动最小延迟
MAX_DELAY = float(os.environ.get("NL_MAX_DELAY", "5"))     # 手动最大延迟
HEADLESS = os.environ.get("NL_HEADLESS", "true").lower() == "true"  # 是否启用无头模式
NLCookie = os.environ.get("NL_COOKIE")                   # 格式: cookie#token 换行分隔
TOPICS_URL = os.environ.get("NL_TOPICS_URL", "https://nodeloc.cc/new")  # 帖子列表页 URL
ENABLE_SCREENSHOT = os.environ.get("NL_ENABLE_SCREENSHOT", "false").lower() == "true"  # 是否启用截图
LOG_LEVEL = os.environ.get("NL_LOG_LEVEL", "INFO").upper()  # 日志级别

# -------------------------------
# 初始化日志系统
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)
# 设置日志输出等级
log.setLevel(logging.INFO if LOG_LEVEL == "INFO" else logging.DEBUG)

# 截图目录
screenshot_dir = "/ql/data/photo"
if not os.path.exists(screenshot_dir):
    os.makedirs(screenshot_dir)
def generate_screenshot_path(filename_prefix, post_id=None):
    """生成截图文件路径"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    if post_id:
        return os.path.join(screenshot_dir, f"{filename_prefix}_{post_id}_{timestamp}.png")
    else:
        return os.path.join(screenshot_dir, f"{filename_prefix}_{timestamp}.png")

# -------------------------------
# 解析多个账号
# -------------------------------
def parse_accounts(cookie_text):
    lines = cookie_text.strip().split("\n")
    accounts = []
    for line in lines:
        parts = line.strip().split("#", 1)
        if len(parts) == 2:
            cookie_str, token = parts
            accounts.append({
                "cookie": cookie_str,
                "token": token
            })
    return accounts

def check_login_status(driver):
    log.debug("🔐 正在检测登录状态...")
    try:
        # 等待指定元素加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "current-user"))
        )
        log.info("✅ 登录状态正常")
        return True
    except:
        log.error(f"❌ 登录失败或 Cookie 无效，请检查你的 Cookie 设置: {e}")
        if ENABLE_SCREENSHOT:
            screenshot_path = generate_screenshot_path('login_failed')
            driver.save_screenshot(screenshot_path)
            log.info(f"📸 已保存登录失败截图：{screenshot_path}")
        return False
# -------------------------------
# 初始化浏览器并设置 Cookie
# -------------------------------
def setup_browser_with_account(account):
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36')

    if HEADLESS:
        log.debug("🌙 启用无头模式")
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')

    #driver = uc.Chrome(options=options)
    driver = uc.Chrome(
        options=options,
        driver_executable_path='/usr/bin/chromedriver',
        version_main=138
    )
    driver.set_window_size(1920, 1080)

    if HEADLESS:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    log.debug("🌐 打开主页 https://nodeloc.cc/")
    driver.get('https://nodeloc.cc/')
    time.sleep(3)

    log.debug("🍪 设置 Cookie")
    for cookie_item in account["cookie"].strip().split(";"):
        try:
            name, value = cookie_item.strip().split("=", 1)
            driver.add_cookie({
                'name': name,
                'value': value,
                'domain': '.nodeloc.cc',
                'path': '/',
                'secure': False,
                'httpOnly': False
            })
        except Exception as e:
            log.info(f"[⚠️] 添加 Cookie 出错：{e}")
            continue

    log.debug("🔄 刷新页面以应用 Cookie")
    driver.refresh()
    time.sleep(5)

    return driver

# -------------------------------
# 获取最近的帖子链接
# -------------------------------
def get_recent_topics(driver):
    log.debug(f"🔍 正在获取最近的 {MAX_TOPICS} 个帖子地址...")
    driver.get(TOPICS_URL)
    time.sleep(5)

    try:
        # 等待内容加载完成
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".topic-list-body .topic-list-item"))
        )

        # 找到所有帖子链接
        elements = driver.find_elements(By.CSS_SELECTOR, ".topic-list-body .topic-list-item a.title")
        unique_links = list(set([elem.get_attribute("href") for elem in elements]))[:MAX_TOPICS]

        if not unique_links:
            log.error("[⚠️] 未能成功获取到任何帖子链接，将保存当前页面截图用于调试")
            if ENABLE_SCREENSHOT:
                driver.save_screenshot('error_screenshot.png')

        log.info(f"📌 共获取到 {len(unique_links)} 个帖子")
        for idx, link in enumerate(unique_links, 1):
            log.debug(f"{idx}. {link}")
        return unique_links
    except Exception as e:
        log.error(f"[❌] 获取帖子失败：{e}")
        if ENABLE_SCREENSHOT:
            driver.save_screenshot('error_screenshot.png')
        return []

# -------------------------------
# 点赞
# -------------------------------
def like_first_post(driver, post_url=None):
    log.debug("❤️ 尝试点赞第一个帖子...")
    try:
        # 等待点赞按钮出现，并确保可点击
        like_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".discourse-reactions-reaction-button .reaction-button"))
        )

        # 提取帖子ID用于截图命名
        try:
            post_id = post_url.split("/")[-1] if post_url else "unknown"
        except Exception as e:
            log.warning(f"[⚠️] 提取 post_id 失败：{e}")
            post_id = "unknown"

        # 截图保存当前页面（使用帖子ID或URL片段作为文件名的一部分）
        if ENABLE_SCREENSHOT:
            before_screenshot_path = generate_screenshot_path('before_like', post_id=post_id)
            driver.save_screenshot(before_screenshot_path)
            log.info(f"📸 已保存点赞前截图：{before_screenshot_path}")

        # 检查是否已经点赞
        svg_use_href = like_button.find_element(By.CSS_SELECTOR, "svg > use").get_attribute("href")
        button_title = like_button.get_attribute("title")

        if "far-heart" in svg_use_href and button_title == "点赞此帖子":
            # 当前未点赞，执行点赞操作
            actions = ActionChains(driver)
            actions.move_to_element(like_button).click().perform()
            log.debug("✅ 成功点赞")

            time.sleep(2)  # 等待点赞动画完成

            # 再次截图保存点赞后的页面
            if ENABLE_SCREENSHOT:
                after_screenshot_path = generate_screenshot_path('after_like', post_id=post_id)
                driver.save_screenshot(after_screenshot_path)
                log.info(f"📸 已保存点赞后截图：{after_screenshot_path}")

            # 🔁 重新查找按钮和 SVG 来验证状态
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".discourse-reactions-reaction-button .reaction-button"))
            )
            new_like_button = driver.find_element(By.CSS_SELECTOR, ".discourse-reactions-reaction-button .reaction-button")
            new_svg_use_href = new_like_button.find_element(By.CSS_SELECTOR, "svg > use").get_attribute("href")
            new_button_title = new_like_button.get_attribute("title")

            if "heart" in new_svg_use_href and new_button_title == "移除此赞":
                log.debug("👍 点赞验证成功")
                return True
            else:
                log.debug("⚠️ 点赞后验证失败")
                return False
        else:
            log.debug("⚠️ 已点赞，跳过")
            return False

    except StaleElementReferenceException:
        log.warning("🔁 元素已刷新，重新查找中...")
        return like_first_post(driver, post_url)
    except Exception as e:
        log.error(f"❌ 点赞失败：{e}")
        if ENABLE_SCREENSHOT:
            error_screenshot_path = os.path.join(screenshot_dir, f"error_like_{post_id}.png")
            driver.save_screenshot(error_screenshot_path)
            log.info(f"📸 已保存错误截图：{error_screenshot_path}")
        return False

# -------------------------------
# 访问单个帖子
# -------------------------------
def visit_topic(driver, topic_url):
    log.debug(f"🌐 正在访问帖子：{topic_url}")
    driver.get(topic_url)

    # 先等待指定随机延迟
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    log.debug(f"⏱️ 随机等待 {delay:.2f} 秒...")
    time.sleep(delay)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        title = driver.title
        log.info(f"[✅] 成功访问帖子：{title}")

        # 执行点赞操作
        try:
            if like_first_post(driver, post_url=topic_url):
                log.info("👍 成功点赞该帖子")
            else:
                log.info("⚠️ 未找到可点赞按钮或已点赞")
        except Exception as e:
            log.warning(f"⚠️ 点赞过程中发生错误：{e}")

    except Exception as e:
        log.error(f"[❌] 访问帖子出错：{e}")

# -------------------------------
# 主函数
# -------------------------------
def main():
    if not NLCookie:
        log.error("❌ 未找到 NLCookie 环境变量，程序退出")
        return

    accounts = parse_accounts(NLCookie)  # 解析出所有账号
    log.info(f'✅ 共查找到 {len(accounts)} 个账号')

    for idx, account in enumerate(accounts, start=1):
        log.info(f"\n🔄 正在使用第 {idx} 个账号执行任务...")
        driver = setup_browser_with_account(account)
        if not check_login_status(driver):
            log.warning("🛑 登录失败，跳过此账号")
            driver.quit()
            continue

        topics = get_recent_topics(driver)
        if not topics:
            log.warning("❌ 没有获取到任何帖子地址")
            driver.quit()
            continue

        log.info("\n🔁 开始顺序访问每个帖子...")
        for topic in topics:
            visit_topic(driver, topic)
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        log.info("🎉 当前账号任务完成！")
        driver.quit()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log.error(f'[💥] 主程序运行时出现错误: {e}')
