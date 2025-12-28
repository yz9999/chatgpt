import asyncio
import re
import random
import string
import requests
import sys
import os
from playwright.async_api import async_playwright

# ================= 配置区 =================
# 在这里填入你的验证链接
TARGET_VERIFY_URL = "https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?verificationId=694fe84f83811641c6e3df71"
# ==========================================

MAIL_TM_API = "https://api.mail.tm"
CMOHS_URL = "https://www.cmohs.org/recipients/page/1?deceased=No"

def get_cmohs_recipient():
    """爬虫：提取 CMOHS 实时姓名"""
    print("[*] 正在同步 CMOHS 数据库...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(CMOHS_URL, headers=headers, timeout=15)
        names_raw = re.findall(r'/recipients/([a-z-]+)"', resp.text)
        valid_names = [n for n in names_raw if n not in ['medal-of-honor', 'latest-news', 'archive']]
        if valid_names:
            parts = random.choice(valid_names).replace("-", " ").split()
            if len(parts) >= 2: return parts[0].upper(), parts[-1].upper()
        return ("BRITT", "SLABINSKI")
    except:
        return ("JAMES", "MILLER")

async def check_page_status(page):
    content = await page.content()
    if any(x in page.url or x in content for x in ["chatgpt.com", "Success", "success"]): return "SUCCESS"
    if "Verification Limit Exceeded" in content: return "LIMIT_EXCEEDED"
    if "collectDocuments" in content or "upload" in content.lower(): return "COLLECT_DOCS"
    return "STAYED"

async def run_verify_flow():
    if "verificationId=" not in TARGET_VERIFY_URL:
        print("[-] 错误：TARGET_VERIFY_URL 似乎不是有效的验证链接")
        return

    v_id = re.search(r'verificationId=([a-z0-9]+)', TARGET_VERIFY_URL).group(1)
    fname, lname = get_cmohs_recipient()
    
    async with async_playwright() as p:
        # GitHub 环境必须开启 headless
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. 初始访问
        print(f"[*] 启动验证流程，ID: {v_id}")
        await page.goto(TARGET_VERIFY_URL, wait_until="networkidle")
        
        # 2. 准备临时邮箱
        domain = requests.get(f"{MAIL_TM_API}/domains").json()['hydra:member'][0]['domain']
        email = f"{''.join(random.choices(string.ascii_lowercase, k=8))}@{domain}"
        requests.post(f"{MAIL_TM_API}/accounts", json={"address": email, "password": "Password123!"})
        token = requests.post(f"{MAIL_TM_API}/token", json={"address": email, "password": "Password123!"}).json()['token']
        print(f"[+] 使用邮箱: {email}")

        # 3. 协议提交 (SheerID API)
        session = requests.Session()
        session.post(f"https://services.sheerid.com/rest/v2/verification/{v_id}/step/collectMilitaryStatus", json={"status": "VETERAN"})
        payload = {
            "firstName": fname, "lastName": lname, "email": email, 
            "birthDate": "1960-05-15", "organization": {"id": "4070"}, 
            "dischargeDate": "2025-05-20", "locale": "en-US"
        }
        r_sub = session.post(f"https://services.sheerid.com/rest/v2/verification/{v_id}/step/collectInactiveMilitaryPersonalInfo", json=payload)
        
        if "limitExceeded" in r_sub.text:
            print("🛑 触发频率限制 (IP被封)")
            await browser.close(); return

        # 4. 轮询邮件
        print("[*] 等待邮件确认函...")
        confirm_link = None
        for _ in range(15):
            await asyncio.sleep(6)
            m_list = requests.get(f"{MAIL_TM_API}/messages", headers={"Authorization": f"Bearer {token}"}).json()
            if m_list.get('hydra:member'):
                msg_id = m_list['hydra:member'][0]['id']
                detail = requests.get(f"{MAIL_TM_API}/messages/{msg_id}", headers={"Authorization": f"Bearer {token}"}).json()
                match = re.search(r'href="(https://services\.sheerid\.com/verify/[^"]+)"', str(detail.get('html')))
                if match:
                    confirm_link = match.group(1).replace("&amp;", "&")
                    break
        
        if confirm_link:
            print("[+] 捕获链接，执行最终激活...")
            await page.goto(confirm_link, wait_until="networkidle")
            await asyncio.sleep(10)
            print(f"【最终结果】: {await check_page_status(page)}")
        else:
            print("[-] 邮件获取失败")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verify_flow())
