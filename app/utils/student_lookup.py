import csv
import os

# 读取学生信息 CSV 并构建学号->姓名映射
csv_path = os.path.join(os.path.dirname(__file__), "../data/students_info.csv")
student_map = {}

try:
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sno = row["学生学号"].strip()
            sname = row["学生姓名"].strip()
            student_map[sno] = sname
except Exception as e:
    print(f"❌ 加载学生信息失败: {e}")

def get_student_name(sno):
    return student_map.get(sno, "未知姓名")
