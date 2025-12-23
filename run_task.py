import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- 配置区 ---
DATA_FILE = "veterans_list.txt"     
LOG_FILE = "used_records.txt"      
FIXED_EMAIL = "6609993@gmail.com"  
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
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 25)

    try:
        if not os.path.exists(DATA_FILE):
            print(f"Error: {DATA_FILE} not found!")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if "|" not in line: continue
            service_branch, full_name, dob, dor = [p.strip() for p in line.split("|")]
            
            if is_already_used(FIXED_EMAIL, full_name):
                print(f">> [SKIP] {full_name}")
                continue

            print(f">> [START] Processing: {full_name}")
            driver.get(TARGET_URL)
            time.sleep(5) # 基础加载等待

            # 1. 处理 Iframe
            if len(driver.find_elements(By.TAG_NAME, "iframe")) > 0:
                driver.switch_to.frame(0)
                print("Switch to iframe.")

            try:
                # 2. 状态选择
                status_el = wait.until(EC.element_to_be_clickable((By.ID, "status")))
                Select(status_el).select_by_visible_text("Military Veteran or Retiree")

                # 3. 军种选择
                branch_el = wait.until(EC.element_to_be_clickable((By.ID, "service_branch")))
                Select(branch_el).select_by_visible_text(service_branch)

                # 4. 姓名
                parts = full_name.split()
                first_n, last_n = parts[0], parts[-1]
                driver.find_element(By.ID, "firstName").send_keys(first_n)
                driver.find_element(By.ID, "lastName").send_keys(last_n)

                # 5. 生日
                y, m, d = dob.split('/')
                Select(driver.find_element(By.ID, "birthDate_month")).select_by_value(str(int(m)))
                driver.find_element(By.ID, "birthDate_day").send_keys(d)
                driver.find_element(By.ID, "birthDate_year").send_keys(y)

                # 6. 退役日
                ry, rm, rd = dor.split('/')
                Select(driver.find_element(By.ID, "dischargeDate_month")).select_by_value(str(int(rm)))
                driver.find_element(By.ID, "dischargeDate_day").send_keys(rd)
                driver.find_element(By.ID, "dischargeDate_year").send_keys(ry)

                # 7. 邮箱
                email_f = driver.find_element(By.ID, "email")
                email_f.clear()
                email_f.send_keys(FIXED_EMAIL)

                # 8. 提交
                submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
                driver.execute_script("arguments[0].click();", submit)
                
                time.sleep(8) # 等待结果页面加载
                mark_as_used(FIXED_EMAIL, full_name)
                print(f"OK: {full_name} submitted.")

            except Exception as e:
                print(f"Internal error for {full_name}: {e}")
                driver.save_screenshot(f"fail_{full_name}.png")

    except Exception as e:
        print(f"Global error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
