import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 基础配置 ---
DATA_FILE = "veterans_list.txt"     
LOG_FILE = "used_records.txt"      
FIXED_EMAIL = "6609993@gmail.com"  
# 使用您提供的具体验证链接
TARGET_URL = "https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?verificationId=694b1244e54a8f0b04283935"

def is_already_used(email, name):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return f"{email}|{name}" in f.read()

def mark_as_used(email, name):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{email}|{name}\n")

def run_automation():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")    
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # 关键：伪装成真实浏览器，避免被 SheerID 直接拦截
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # 增加等待时间至 30 秒，应对云端网络波动
    wait = WebDriverWait(driver, 30)

    try:
        if not os.path.exists(DATA_FILE):
            print("Error: veterans_list.txt not found!")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if "|" not in line: continue
            service_branch, full_name, dob, dor = [p.strip() for p in line.split("|")]
            
            if is_already_used(FIXED_EMAIL, full_name):
                print(f">> [跳过] {full_name}")
                continue

            print(f">> [正在处理] {full_name}")
            driver.get(TARGET_URL)
            time.sleep(5) # 给页面充足的加载时间

            # --- 关键修复：处理可能存在的 iframe ---
            if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
                driver.switch_to.frame(0)
                print("检测到 iframe，已切换。")

            try:
                # 1. Status 选择 (Military Veteran or Retiree)
                # 使用更加稳健的定位方式
                status_box = wait.until(EC.element_to_be_clickable((By.ID, "status")))
                status_box.click()
                time.sleep(1)
                # 针对某些页面使用 Select 类的处理
                Select(status_box).select_by_visible_text("Military Veteran or Retiree")

                # 2. 军种选择
                branch_box = wait.until(EC.element_to_be_clickable((By.ID, "service_branch")))
                Select(branch_box).select_by_visible_text(service_branch)

                # 3. 姓名填写
                first_name = full_name.split()[0]
                last_name = full_name.split()[-1]
                driver.find_element(By.ID, "firstName").send_keys(first_name)
                driver.find_element(By.ID, "lastName").send_keys(last_name)

                # 4. 出生日期
                dob_y, dob_m, dob_d = dob.split('/')
                Select(driver.find_element(By.ID, "birthDate_month")).select_by_value(str(int(dob_m)))
                driver.find_element(By.ID, "birthDate_day").send_keys(dob_d)
                driver.find_element(By.ID, "birthDate_year").send_keys(dob_y)

                # 5. 退役日期
                dor_y, dor_m, dor_d = dor.split('/')
                Select(driver.find_element(By.ID, "dischargeDate_month")).select_by_value(str(int(dor_m)))
                driver.find_element(By.ID, "dischargeDate_day").send_keys(dor_d)
                driver.find_element(By.ID, "dischargeDate_year").send_keys(dor_y)

                # 6. 邮箱
                email_input = driver.find_element(By.ID, "email")
                email_input.clear()
                email_input.send_keys(FIXED_EMAIL)

                # 7. 提交按钮 - SheerID 按钮 ID 可能是 'submit' 或带有特定 class
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
                
                # 使用 JavaScript 强制点击，防止按钮被浮层遮挡
                driver.execute_script("arguments[0].click();", submit_btn)
                
                # 验证是否提交成功（检查页面是否跳转或出现成功提示）
                time.sleep(5)
                mark_as_used(FIXED_EMAIL, full_name)
                print(f"ok: {full_name} 提交成功")

            except Exception as e:
                print(f"填写 {full_name} 时发生内部错误: {e}")
                # 截个图方便调试（在 GitHub Actions 的 Artifacts 中查看）
                driver.save_screenshot(f"error_{full_name}.png")

    except Exception as e:
        print(f"全局错误: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
