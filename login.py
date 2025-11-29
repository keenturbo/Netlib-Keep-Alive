import os
import time
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 日志缓冲
log_buffer = []

def log(msg):
    """统一日志输出"""
    print(msg)
    log_buffer.append(msg)

# 从环境变量解析账号
accounts_env = os.environ.get("SITE_ACCOUNTS", "")
accounts = []

for item in accounts_env.split(";"):
    if item.strip():
        try:
            username, password = item.split(",", 1)
            accounts.append({"username": username.strip(), "password": password.strip()})
        except ValueError:
            log(f"⚠️ 忽略格式错误的账号项: {item}")

# 失败消息匹配
fail_msgs = [
    "Invalid credentials.",
    "Not connected to server.",
    "Error with the login: login size should be between 2 and 50 (currently: 1)"
]

def send_tg_log():
    """发送 Telegram 日志（支持分块发送）"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        log("⚠️ Telegram 未配置，跳过推送")
        return

    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)
    now_str = beijing_now.strftime("%Y-%m-%d %H:%M:%S") + " UTC+8"

    final_msg = f"📌 Netlib 保活执行日志\n🕒 {now_str}\n\n" + "\n".join(log_buffer)

    # 分块发送，单条消息最大 4096 字符
    for i in range(0, len(final_msg), 3900):
        chunk = final_msg[i:i+3900]
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/sendMessage",
                params={"chat_id": chat_id, "text": chunk},
                timeout=10
            )
            if resp.status_code == 200:
                log(f"✅ Telegram 推送成功 [第 {i//3900 + 1} 块]")
            else:
                log(f"⚠️ Telegram 推送失败 [第 {i//3900 + 1} 块]: HTTP {resp.status_code}, {resp.text}")
        except Exception as e:
            log(f"⚠️ Telegram 推送异常 [第 {i//3900 + 1} 块]: {e}")

def login_account(context, username, password, attempt=1):
    """
    单账号登录逻辑（支持重试）
    :param context: Playwright 浏览器上下文
    :param username: 用户名
    :param password: 密码
    :param attempt: 当前重试次数
    """
    max_retries = 3
    log(f"🚀 开始登录账号: {username} (尝试 {attempt}/{max_retries})")
    
    page = None
    try:
        page = context.new_page()
        
        # 动态等待页面加载
        page.goto("https://www.netlib.re/", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # 点击登录按钮
        page.wait_for_selector("text=Login", timeout=10000)
        page.get_by_text("Login").click()
        
        # 填写用户名
        page.wait_for_selector("input[name='username'], [role='textbox'][name*='Username']", timeout=10000)
        page.get_by_role("textbox", name="Username").fill(username)
        time.sleep(1)
        
        # 填写密码
        page.get_by_role("textbox", name="Password").fill(password)
        time.sleep(1)
        
        # 提交表单
        page.get_by_role("button", name="Validate").click()
        page.wait_for_load_state("networkidle", timeout=15000)
        
        # 判断登录结果
        success_text = "You are the exclusive owner of the following domains."
        if page.query_selector(f"text={success_text}"):
            log(f"✅ 账号 {username} 登录成功")
            time.sleep(3)  # 保活停留
            return True
        else:
            # 检查已知错误
            failed_msg = None
            for msg in fail_msgs:
                if page.query_selector(f"text={msg}"):
                    failed_msg = msg
                    break
            
            if failed_msg:
                log(f"❌ 账号 {username} 登录失败: {failed_msg}")
            else:
                log(f"❌ 账号 {username} 登录失败: 未知错误")
            return False
            
    except PlaywrightTimeout as e:
        log(f"⏱️ 账号 {username} 超时: {e}")
        # 指数退避重试
        if attempt < max_retries:
            wait_time = 2 ** attempt
            log(f"🔄 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            return login_account(context, username, password, attempt + 1)
        else:
            log(f"❌ 账号 {username} 重试失败，已达最大重试次数")
            return False
            
    except Exception as e:
        log(f"❌ 账号 {username} 登录异常: {type(e).__name__}: {e}")
        # 非超时异常也重试
        if attempt < max_retries:
            wait_time = 2 ** attempt
            log(f"🔄 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            return login_account(context, username, password, attempt + 1)
        else:
            log(f"❌ 账号 {username} 重试失败")
            return False
    finally:
        if page:
            page.close()

def run():
    """主执行函数"""
    if not accounts:
        log("⚠️ 未配置任何账号，请检查 SITE_ACCOUNTS 环境变量")
        return
    
    with sync_playwright() as playwright:
        # 启动浏览器（复用浏览器实例）
        browser = playwright.chromium.launch(headless=True)
        
        success_count = 0
        fail_count = 0
        
        for acc in accounts:
            # 每个账号使用独立的浏览器上下文
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            result = login_account(context, acc["username"], acc["password"])
            
            if result:
                success_count += 1
            else:
                fail_count += 1
            
            context.close()
            time.sleep(2)  # 账号间隔
        
        browser.close()
        
        # 汇总统计
        log(f"\n📊 执行统计：成功 {success_count} 个，失败 {fail_count} 个")

if __name__ == "__main__":
    run()
    send_tg_log()