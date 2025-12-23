import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# --- 基础配置 ---
DATA_FILE = "veterans_list.txt"     # 原始数据文件
LOG_FILE = "used_records.txt"      # 已使用信息记录文件
FIXED_EMAIL = "6609993@gmail.com"  # 您的固定邮箱
TARGET_URL = "https://example.com" # !!! 请替换为实际的验证网址 !!!

# --- 核心功能函数 ---

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
    # 配置浏览器选项
    chrome_options = Options()
    # 如果在 GitHub Actions 运行，请取消下面一行的注释
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 读取原始数据
        if not os.path.exists(DATA_FILE):
            print(f"错误: 找不到数据文件 {DATA_FILE}")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if "|" not in line: continue
            
            # 解析：军种 | 姓名 | 出生日期 | 退役日期
            parts = [p.strip() for p in line.split("|")]
            service, name, dob, dor = parts
            
            # 2. 自动屏蔽逻辑
            if is_already_used(FIXED_EMAIL, name):
                print(f">> [跳过] {name} 已经使用过。")
                continue

            print(f">> [开始处理] 正在为 {name} 填写表单...")
            
            # 3. 访问网页
            driver.get(TARGET_URL)
            
            # --- SheerID 填写逻辑 ---
            
            # A. 选择 Status (Military Veteran or Retiree)
            status_box = wait.until(EC.element_to_be_clickable((By.ID, "status")))
            status_box.click()
            time.sleep(0.5)
            driver.find_element(By.XPATH, "//option[contains(text(), 'Military Veteran or Retiree')]").click()

            # B. 选择 Branch of service
            branch_box = driver.find_element(By.ID, "service_branch")
            branch_box.click()
            time.sleep(0.5)
            driver.find_element(By.XPATH, f"//option[text()='{service}']").click()

            # C. 填写姓名
            first_name = name.split()[0]
            last_name = name.split()[-1]
            driver.find_element(By.ID, "firstName").send_keys(first_name)
            driver.find_element(By.ID, "lastName").send_keys(last_name)

            # D. 填写出生日期 (格式: YYYY/MM/DD)
            dob_y, dob_m, dob_d = dob.split('/')
            Select(driver.find_element(By.ID, "birthDate_month")).select_by_value(str(int(dob_m)))
            driver.find_element(By.ID, "birthDate_day").send_keys(dob_d)
            driver.find_element(By.ID, "birthDate_year").send_keys(dob_y)

            # E. 填写退役日期 (格式: 2025/MM/DD)
            dor_y, dor_m, dor_d = dor.split('/')
            Select(driver.find_element(By.ID, "dischargeDate_month")).select_by_value(str(int(dor_m)))
            driver.find_element(By.ID, "dischargeDate_day").send_keys(dor_d)
            driver.find_element(By.ID, "dischargeDate_year").send_keys(dor_y)

            # F. 填写邮箱
            email_field = driver.find_element(By.ID, "email")
            email_field.clear()
            email_field.send_keys(FIXED_EMAIL)

            # G. 提交表单 (请确认 ID 是否正确，通常是 'submit')
            # driver.find_element(By.ID, "submit").click()
            
            # 4. 成功后记录
            mark_as_used(FIXED_EMAIL, name)
            print(f"ok: {name} 填写完成并记录。")
            
            # 每个任务间隔，防止被封
            time.sleep(5) 

    except Exception as e:
        print(f"运行时发生错误: {e}")
    finally:
        print("所有任务执行完毕。")
        driver.quit()

if __name__ == "__main__":
    run_automation()
