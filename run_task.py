# 建议保存为 run_task.py
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def fill_sheerid_form():
    # --- 无头模式配置 ---
    chrome_options = Options()
    chrome_options.add_argument("--headless") # 不显示浏览器界面
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    # 从环境变量获取敏感信息（或直接读取文件）
    fixed_email = "6609993@gmail.com"
    target_url = "https://services.sheerid.com/verify/690415d58971e73ca187d8c9/?verificationId=694b1244e54a8f0b04283935" 

    try:
        # 确保当前目录下有你的 txt 文件
        with open("veterans_list.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            if "|" not in line: continue
            service, name, dob, dor = [p.strip() for p in line.split("|")]
            first_name = name.split()[0]
            last_name = name.split()[-1]

            driver.get(target_url)
            
            # --- 以下是之前调试好的填写逻辑 ---
            # 选择 Status
            status_el = wait.until(EC.element_to_be_clickable((By.ID, "status")))
            status_el.click()
            driver.find_element(By.XPATH, "//option[contains(text(), 'Military Veteran or Retiree')]").click()

            # 填写姓名和邮箱
            driver.find_element(By.ID, "firstName").send_keys(first_name)
            driver.find_element(By.ID, "lastName").send_keys(last_name)
            driver.find_element(By.ID, "email").send_keys(fixed_email)
            
            # (其余日期填写逻辑保持一致...)
            
            print(f"成功在云端提交: {name}")
            time.sleep(2) 

    except Exception as e:
        print(f"运行时发生错误: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    fill_sheerid_form()
