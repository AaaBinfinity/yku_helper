from bs4 import BeautifulSoup

def get_grades(session):
    query_url = "https://jwgl.yku.edu.cn/jsxsd/kscj/cjcx_list"
    form_data = {
        "kksj": "2023-2024-2",
        "kcxz": "10",
        "kcmc": "",
        "xsfs": "all"
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
