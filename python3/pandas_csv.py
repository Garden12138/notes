import pandas as pd

def export_csv(data: list, filename: str) -> None:
    if data is None or len(data) == 0:
        return
    # 获取列名
    keys = data[0].keys()
    # 创建每列字典
    columns = {}
    for key in keys:
        columns[key] = []
    # 填充每列字典
    for row in data:
        for key in keys:
            columns[key].append(row[key])
    # 导出csv文件
    df = pd.DataFrame(columns)
    df.to_csv('./' + filename + '.csv', index=False, encoding='utf-8-sig')

# 测试
data = [
    {'name': 'Alice', 'age': 20},
    {'name': 'Bob', 'age': 25},
    {'name': 'Charlie', 'age': 30}
]
export_csv(data, 'csv_test')