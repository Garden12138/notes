from zhdate import ZhDate as lunar_date
from datetime import datetime
import re

def lunar_to_solar(lunar_date_str: str) -> str:
    # 使用正则表达式匹配月份和日期
    match = re.search(r'农历(\d+)月(\d+)日', input_string)
    if match:
        # 提取月份和日期
        month = match.group(1)
        day = match.group(2)
    else:
        # 如果没有匹配到，打印错误信息
        raise ValueError("输入的字符串格式不正确")
    lunar = lunar_date(int(datetime.now().year), int(month), int(day))
    solar = lunar.to_datetime().strftime('%Y-%m-%d')
    print(f'{lunar}转换成新历{solar}')
    return solar

# 执行
input_string = "农历1月1日"
print(lunar_to_solar(input_string))



