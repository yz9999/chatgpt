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
DATA_FILE = "veterans_list.txt"     # 存放 100 位老兵数据的文件
LOG_FILE = "used_records.txt"      # 存放已成功提交记录的文件
FIXED_EMAIL = "6609993@gmail.com"  # 您的固定邮箱
TARGET_URL = "https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?verificationId=694b1244e54a8f0b04283935" # !!! 请替换为实际的 SheerID 验证网址 !!!

def is_already_used(email, name):
    """检查 邮箱+姓名 是否已经成功提交过"""
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        used_data = f.read()
        return f"{email}|{name}" in used_data

def mark_as_used(email, name):
    """记录已成功提交的信息"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{email}|{name}\n")

def run_automation():
    # --- GitHub Actions 专用浏览器配置 ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # 必须使用无头模式
    chrome_options.add_argument("--no-sandbox")    # 禁用沙盒，解决权限问题
    chrome_options.add_argument("--disable-dev-shm-usage") # 解决内存限制问题
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 自动安装并配置匹配的 ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        if not os.path.exists(DATA_FILE):
            print(f"错误: 找不到数据文件 {DATA_FILE}")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if "|" not in line: continue
            
            # 解析：军种 | 姓名 | 出生日期 | 退役日期
            service_branch, full_name, dob, dor = [p.strip() for p in line.split("|")]
            
            # 自动屏蔽逻辑
            if is_already_used(FIXED_EMAIL, full_name):
                print(f">> [已屏蔽] {full_name} 之前已提交过。")
                continue

            print(f">> [正在处理] 姓名: {full_name} | 军种: {service_branch}")
            
            driver.get(TARGET_URL)
            
            # 1. 选择 Status (固定为 Military Veteran or Retiree)
            status_box = wait.until(EC.element_to_be_clickable((By.ID, "status")))
            status_box.click()
            time.sleep(1)
            driver.find_element(By.XPATH, "//option[contains(text(), 'Military Veteran or Retiree')]").click()

            # 2. 选择 Branch of service
            branch_box = driver.find_element(By.ID, "service_branch")
            branch_box.click()
            time.sleep(1)
            driver.find_element(By.XPATH, f"//option[text()='{service_branch}']").click()

            # 3. 填写姓名
            first_name = full_name.split()[0]
            last_name = full_name.split()[-1]
            driver.find_element(By.ID, "firstName").send_keys(first_name)
            driver.find_element(By.ID, "lastName").send_keys(last_name)

            # 4. 填写出生日期 (YYYY/MM/DD)
            dob_y, dob_m, dob_d = dob.split('/')
            Select(driver.find_element(By.ID, "birthDate_month")).select_by_value(str(int(dob_m)))
            driver.find_element(By.ID, "birthDate_day").send_keys(dob_d)
            driver.find_element(By.ID, "birthDate_year").send_keys(dob_y)

            # 5. 填写退役日期 (YYYY/MM/DD)
            dor_y, dor_m, dor_d = dor.split('/')
            Select(driver.find_element(By.ID, "dischargeDate_month")).select_by_value(str(int(dor_m)))
            driver.find_element(By.ID, "dischargeDate_day").send_keys(dor_d)
            driver.find_element(By.ID, "dischargeDate_year").send_keys(dor_y)

            # 6. 填写邮箱
            email_input = driver.find_element(By.ID, "email")
            email_input.clear()
            email_input.send_keys(FIXED_EMAIL)

            # 7. 提交表单 (点击 Verify My Eligibility)
            # 注意：实际生产中请取消下面一行的注释
            # driver.find_element(By.ID, "submit").click()
            
            # 8. 成功后记录
            mark_as_used(FIXED_EMAIL, full_name)
            print(f"ok: {full_name} 处理成功。")
            
            time.sleep(3) # 短暂休眠

    except Exception as e:
        print(f"运行时报错: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
