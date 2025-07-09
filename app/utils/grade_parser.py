from bs4 import BeautifulSoup

def get_grades(session, kksj="", kcxz="", kcmc="", xsfs="all"):
    """
    获取学生成绩。

    参数说明:
    - session: 登录后的 requests.Session 对象
    - kksj: 开课学期
    - kcxz: 课程性质
    - kcmc: 课程名称关键词（默认空字符串）
    - xsfs: 显示方式（默认 "all" 表示全部）
    """
    query_url = "https://jwgl.yku.edu.cn/jsxsd/kscj/cjcx_list"

    form_data = {
        "kksj": kksj,
        "kcxz": kcxz,
        "kcmc": kcmc,
        "xsfs": xsfs
    }

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': "https://jwgl.yku.edu.cn/jsxsd/kscj/cjcx_query",
        'Origin': 'https://jwgl.yku.edu.cn',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    resp = session.post(query_url, data=form_data, headers=headers, verify=False)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", id="dataList")
    if not table:
        return []

    rows = []
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    for row in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if cols:
            rows.append(dict(zip(headers, cols)))

    return rows
