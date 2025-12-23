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
TARGET_URL = "https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?verificationId=694b1244e54a8f0b04283935" # !!! 请在此处填写实际的 SheerID 验证地址 !!!

def is_already_used(email, name):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return f"{email}|{name}" in f.read()

def mark_as_used(email, name):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{email}|{name}\n")

def run_automation():
    # 核心修复：确保日志文件在 Git add 之前就存在
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    # --- 浏览器配置 (针对 GitHub Actions 优化) ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")    
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 自动下载驱动
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)

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
                print(f">> [Skipped] {full_name}")
                continue

            print(f">> [Processing] {full_name}")
            driver.get(TARGET_URL)
            
            # 1. Status 选择
            status_box = wait.until(EC.element_to_be_clickable((By.ID, "status")))
            status_box.click()
            time.sleep(1)
            driver.find_element(By.XPATH, "//option[contains(text(), 'Military Veteran or Retiree')]").click()

            # 2. 军种选择
            branch_box = driver.find_element(By.ID, "service_branch")
            branch_box.click()
            time.sleep(1)
            driver.find_element(By.XPATH, f"//option[text()='{service_branch}']").click()

            # 3. 姓名填写
            first_name = full_name.split()[0]
            last_name = full_name.split()[-1]
            driver.find_element(By.ID, "firstName").send_keys(first_name)
            driver.find_element(By.ID, "lastName").send_keys(last_name)

            # 4. 出生日期 (分拆 YYYY/MM/DD)
            dob_y, dob_m, dob_d = dob.split('/')
            Select(driver.find_element(By.ID, "birthDate_month")).select_by_value(str(int(dob_m)))
            driver.find_element(By.ID, "birthDate_day").send_keys(dob_d)
            driver.find_element(By.ID, "birthDate_year").send_keys(dob_y)

            # 5. 退役日期 (分拆 YYYY/MM/DD)
            dor_y, dor_m, dor_d = dor.split('/')
            Select(driver.find_element(By.ID, "dischargeDate_month")).select_by_value(str(int(dor_m)))
            driver.find_element(By.ID, "dischargeDate_day").send_keys(dor_d)
            driver.find_element(By.ID, "dischargeDate_year").send_keys(dor_y)

            # 6. 邮箱
            email_field = driver.find_element(By.ID, "email")
            email_field.clear()
            email_field.send_keys(FIXED_EMAIL)

            # 7. 提交 (确认无误后再取消注释)
            # driver.find_element(By.ID, "submit").click()
            
            mark_as_used(FIXED_EMAIL, full_name)
            print(f"Success: {full_name}")
            time.sleep(5) 

    except Exception as e:
        print(f"Runtime Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
