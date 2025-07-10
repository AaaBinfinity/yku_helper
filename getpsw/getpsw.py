import re
import csv
import os

log_file_path = 'run.log'
output_csv_path = 'login_data.csv'

# 收集完整记录的容器
records = []

# ------------------------------
# 读取已有CSV记录用于去重
existing_records = set()
if os.path.exists(output_csv_path):
    with open(output_csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_records.add((row["学号"], row["姓名"], row["密码"]))

# ------------------------------
# 从日志文件中提取登录成功的数据
with open(log_file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

temp_data = {}

for i, line in enumerate(lines):
    # 记录姓名
    match_name = re.search(r'API登录尝试 - 学号: (\d+), 姓名: ([\u4e00-\u9fa5]+)', line)
    if match_name:
        sno = match_name.group(1)
        name = match_name.group(2)
        temp_data[sno] = {"学号": sno, "姓名": name, "密码": ""}

    # 记录密码
    match_pwd = re.search(r'登录尝试 - 学号: (\d+), 密码: ([^,]+), 验证码:', line)
    if match_pwd:
        sno = match_pwd.group(1)
        pwd = match_pwd.group(2)
        if sno not in temp_data:
            temp_data[sno] = {"学号": sno, "姓名": "", "密码": pwd}
        else:
            temp_data[sno]["密码"] = pwd

    # 检查是否登录成功
    match_success = re.search(r'✅ 登录成功 - 学号: (\d+), 密码: ([^,]+), 验证码:', line)
    if match_success:
        sno = match_success.group(1)
        if sno in temp_data:
            record = temp_data[sno]
            record_tuple = (record["学号"], record["姓名"], record["密码"])
            if record_tuple not in existing_records:
                records.append(record)
                existing_records.add(record_tuple)  # 避免后续重复

# ------------------------------
# 追加写入CSV
if records:
    file_exists = os.path.exists(output_csv_path)
    with open(output_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["学号", "姓名", "密码"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
    print(f"✅ 共写入 {len(records)} 条新记录至 {output_csv_path}")
else:
    print("⚠️ 没有新记录需要写入。")
