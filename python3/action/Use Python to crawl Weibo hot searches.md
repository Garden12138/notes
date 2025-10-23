## 使用 Python 爬取微博热搜数据

### 🌈 介绍

* 一个功能完整的微博热门数据爬虫工具，支持命令行参数控制，可自动爬取不同分类的微博热门数据。

### 🚀 功能特性

- **多模式爬取**: 支持爬取所有分类、指定分类或单个分类
- **命令行控制**: 完整的命令行参数支持，使用灵活
- **智能验证**: 自动验证分类名称有效性
- **异常处理**: 完善的错误处理和重试机制
- **进度跟踪**: 实时显示爬取进度和状态
- **数据清洗**: 自动清洗和格式化微博数据
- **频率控制**: 内置反爬机制，避免被限制

### 📦 安装依赖

```bash
# 安装所需依赖库
pip install -r requirements.txt
```

```requirements.txt```内容如下：

```txt
# 网页解析和数据处理
lxml>=4.9.0
requests>=2.28.0
pandas>=1.5.0
numpy>=1.24.0

# 其他依赖
# email.utils 是Python标准库，无需安装
# argparse 是Python标准库，无需安装
# os 是Python标准库，无需安装
# re 是Python标准库，无需安装
# time 是Python标准库，无需安装
# csv 是Python标准库，无需安装
# random 是Python标准库，无需安装
```

### 🎯 使用方法

* 基本命令格式

  ```bash
  python crawl_weibo.py [模式] [参数]
  ```

* 可用模式

  * 爬取所有分类
    ```bash
    # 使用默认参数（55页，15秒间隔）
    python crawl_weibo.py --all

    # 自定义参数
    python crawl_weibo.py --all --pages 30 --sleep 10
    ```

  * 爬取指定分类
    ```bash
    # 爬取多个分类
    python crawl_weibo.py --categories 搞笑 情感 明星

    # 使用短参数名
    python crawl_weibo.py -c 搞笑 情感 明星 -p 20 -t 5
    ```

  * 爬取单个分类
    ```bash
    # 爬取单个分类
    python crawl_weibo.py --single 房产

    # 使用短参数名
    python crawl_weibo.py -s 房产 -p 30
    ```

  * 查看可用分类
    ```bash
    # 列出所有可用分类
    python crawl_weibo.py --list-categories
    ```

  * 查看帮助
    ```bash
    # 查看详细帮助信息
    python crawl_weibo.py --help
    ```

* 参数说明

  | 参数 | 短参数 | 说明 | 默认值 |
  |------|--------|------|--------|
  | `--all` | `-a` | 爬取所有分类 | - |
  | `--categories` | `-c` | 爬取指定分类（可多个） | - |
  | `--single` | `-s` | 爬取单个分类 | - |
  | `--list-categories` | `-l` | 列出所有可用分类 | - |
  |   `--pages` | `-p` | 每个分类爬取页数 | 55 |
  | `--sleep` | `-t` | 分类间睡眠时间（秒） | 15 |
  | `--output-dir` | `-o` | 输出目录 | ./weiboHot |

### 📊 输出数据

* 数据格式，爬取的数据保存为CSV文件，包含以下字段：

  | 字段名 | 说明 |
  |--------|------|
  | 博主 | 微博发布者昵称 |
  | 发布日期 | 微博发布时间（YYYY-MM-DD HH:MM:SS） |
  | 发布内容 | 微博文本内容（已清洗） |
  | 转发数量 | 微博转发数 |
  | 评论数量 | 微博评论数 |
  | 点赞数量 | 微博点赞数 |
  | 博文链接 | 微博完整链接 |

* 文件命名
  - 文件位置: `./weiboHot/分类名.csv`
  - 编码格式: UTF-8-BOM（兼容Excel中文显示）

### 🔧 技术实现

* 核心流程
  - **参数解析**: 使用argparse解析命令行参数
  - **分类验证**: 验证指定分类是否在支持列表中
  - **URL构造**: 根据分类代码构造微博API请求URL
  - **数据爬取**: 分页爬取微博数据，包含频率控制
  - **数据清洗**: 清洗和格式化爬取的数据
  - **数据保存**: 将数据保存为CSV文件

* 关键组件，分类映射 (`tagDict`)
  ```python
  tagDict = {
      '搞笑': '1028034388',
      '情感': '1028031988',
      '明星': '1028034288',
      # ... 更多分类
  }
  ```

* ```URL```构造规则
  ```
  https://weibo.com/ajax/feed/hottimeline?
  since_id=0&
  refresh={页号}&
  group_id={分类代码}&
  containerid={前缀}_ctg1_{后缀}_-_ctg1_{后缀}&
  extparam=discover%7Cnew_feed&
  max_id={页号-1}&
  count=10
  ```

* 反爬策略
  - 请求间隔: 每页10秒，分类间15秒
  - 超时设置: 30秒请求超时
  - 异常处理: 自动跳过失败请求
  - 用户代理: 模拟真实浏览器请求

### ⚠️ 注意事项

- **Cookie有效性**: 需要定期更新Cookie，避免登录失效
- **请求频率**: 不要设置过短的睡眠时间，避免触发反爬
- **网络稳定**: 确保网络连接稳定，避免请求失败
- **存储空间**: 大量数据需要足够的磁盘空间
- **法律合规**: 请遵守相关法律法规，合理使用爬虫

### 🐛 故障排除

* 常见问题

  * **请求失败**
     - 检查网络连接
     - 更新Cookie
     - 增加睡眠时间

  * **分类不存在**
     - 使用 `--list-categories` 查看可用分类
     - 检查分类名称拼写

  * **数据为空**
     - 检查网络连接
     - 验证Cookie有效性
     - 尝试减少爬取页数

  * **程序中断**
     - 使用Ctrl+C可以安全中断程序
     - 已爬取的数据会自动保存

### 📈 性能优化建议

* **合理设置页数**: 根据需求调整爬取页数
* **调整睡眠时间**: 在稳定性和速度间平衡
* **分批处理**: 大量数据可分多次爬取
* **监控资源**: 注意内存和磁盘使用情况

### 🔄 更新日志

- **v2.0**: 添加命令行参数支持，优化用户体验
- **v1.0**: 基础爬虫功能，支持多分类爬取

### 📞 技术支持

* 如有问题或建议，请检查：
  - 依赖库是否正确安装
  - 网络连接是否正常
  - Cookie是否有效
  - 参数设置是否合理

### 代码示例：

```python

# 游戏
#https://weibo.com/hot/weibo/1028034888
#https://weibo.com/ajax/feed/hottimeline?since_id=0&refresh=1&group_id=1028034888&containerid=102803_ctg1_4888_-_ctg1_4888&extparam=discover%7Cnew_feed&max_id=0&count=10
# 体育
#https://weibo.com/hot/weibo/1028031388
#https://weibo.com/ajax/feed/hottimeline?since_id=0&refresh=1&group_id=1028031388&containerid=102803_ctg1_1388_-_ctg1_1388&extparam=discover%7Cnew_feed&max_id=0&count=10

from lxml import etree
import requests
import random
import time
import csv
import pandas as pd 
import numpy as np
import re
import os
import argparse
from email.utils import parsedate_to_datetime

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    # 
    'Cookie': '_s_tentry=passport.weibo.com; Apache=8263745139655.654.1732005489644; SINAGLOBAL=8263745139655.654.1732005489644; ULV=1732005489654:1:1:1:8263745139655.654.1732005489644:; SCF=AsNY-iT78VFDN8UPJ9Pn1vGa3xqrmvLQTff3GQ82s22S2XlW2Jj1W5zzMZ0WdMtqf9cI7_2YjwcqLVkh8NOLVL4.; SUB=_2A25KORcADeRhGeRG6VoR9ijMyTuIHXVpNxbIrDV8PUNbmtAbLVn2kW9NUg7Y_kBQY0ofI9iNyy8FG2TqkdfErTNM; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5crog3WShEqCMLxGne.Dal5JpX5KzhUgL.FozReon7Soq7eoM2dJLoI7LGqPi.9g4xBH2t; ALF=02_1734669392'
}

tagDict = {
    '搞笑': '1028034388',
    '情感': '1028031988',
    '明星': '1028034288',
    '数码': '1028035088',
    '体育': '1028031388',
    '汽车': '1028035188',
    '电影': '1028033288',
    '游戏': '1028034888',
    '股市': '1028031288',
    '音乐': '1028035288',
    '动漫': '1028032388',
    '军事': '1028036688',
    '美食': '1028032688',
    '电视剧': '1028032488',
    '旅游': '1028032588',
    '运动健身': '1028034788',
    '综艺': '1028034688',
    '美妆': '1028031588',
    '萌宠': '1028032788',
    '电竞': '102803600390',
    '读书': '1028034588',
    '科技': '1028032088',
    '星座': '1028031688',
    '教育': '102803600080',
    '房产': '1028035588',
    '财经': '1028036388',
    '社会': '1028034188'
}

def get_weibo_hot(tag: str, count: int) -> bool:
    """
    爬取指定分类的微博热门数据
    
    Args:
        tag: 分类名称
        count: 爬取页数
        
    Returns:
        bool: 是否爬取成功
    """
    print(f"\n{'='*50}")
    print(f"开始爬取分类：{tag}")
    print(f"{'='*50}")
    
    bz = [] 
    fbrq = [] 
    fbnr = [] 
    zfsl = []
    plsl = []
    dzsl = []
    bwlj = []
    
    tagCode = tagDict.get(tag)
    if not tagCode:
        print(f"错误：未找到分类 '{tag}' 对应的代码")
        return False
        
    tagCodePrefix = tagCode[:6]
    tagCodeSuffix = tagCode[6:]
    
    for num in range(count):
        url = 'https://weibo.com/ajax/feed/hottimeline?since_id=0&refresh=' + str(num + 1) + '&group_id=' + tagCode + '&containerid=' + tagCodePrefix +'_ctg1_' + tagCodeSuffix + '_-_ctg1_' + tagCodeSuffix + '&extparam=discover%7Cnew_feed&max_id=' + str(num) + '&count=10'
        print(f"请求发送：{url}")
        
        try:
            response = requests.get(url=url, headers=headers, timeout=30).json()
            statuses = response.get('statuses', [])
            
            if not statuses:
                print(f"第{num+1}页无数据，跳过")
                continue
                
        except Exception as e:
            print(f"第{num+1}页请求失败：{str(e)}")
            continue
            
        print(f"******************开始爬取第{num+1}页******************")
        
        for i in range(len(statuses)):
            try:
                dt = parsedate_to_datetime(statuses[i].get('created_at')).replace(tzinfo=None)
                formatted_date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                
                user_info = statuses[i].get('user', {})
                screen_name = user_info.get('screen_name', '未知用户')
                user_id = user_info.get('idstr', '')
                
                text_content = statuses[i].get('text', '')
                cleaned_text = re.sub("[A-Za-z0-9\!\%\[\]\,\。\<\=\"\:\/\.\/\?\&\-\>\_\; \_\ ; \']", "", text_content)
                
                print(f"博主：{screen_name}")
                print(f"发布日期：{formatted_date_str}")
                print(f"发布内容：{cleaned_text}")
                print(f"转发数量：{statuses[i].get('reposts_count', 0)}")
                print(f"评论数量：{statuses[i].get('comments_count', 0)}")
                print(f"点赞数量：{statuses[i].get('attitudes_count', 0)}")
                print(f"博文链接：https://weibo.com/{user_id}/{statuses[i].get('mid', '')}")
                
                # 收集数据
                bz.append(screen_name)
                fbrq.append(formatted_date_str)
                fbnr.append(cleaned_text)
                zfsl.append(statuses[i].get('reposts_count', 0))
                plsl.append(statuses[i].get('comments_count', 0))
                dzsl.append(statuses[i].get('attitudes_count', 0))
                bwlj.append(f'https://weibo.com/{user_id}/{statuses[i].get("mid", "")}')
                
            except Exception as e:
                print(f"处理第{i+1}条数据时出错：{str(e)}")
                continue
                
        print(f"******************第{num+1}页爬取成功******************")
        print("睡眠10秒...")  # 频繁发送请求容易被拒绝
        time.sleep(10)
    
    # 保存数据
    if bz:  # 如果有数据才保存
        dt = {'博主':bz, '发布日期':fbrq, '发布内容':fbnr, '转发数量':zfsl, '评论数量':plsl, '点赞数量':dzsl, '博文链接':bwlj}
        df = pd.DataFrame(dt)
        
        # 确保输出目录存在
        output_dir = './weiboHot'
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f'{tag}.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"数据已保存到：{output_file}")
        return True
    else:
        print(f"分类 '{tag}' 没有爬取到任何数据")
        return False


def crawl_all_categories(count: int = 55, sleep_between: int = 15):
    """
    自动爬取所有分类的微博热门数据
    
    Args:
        count: 每个分类爬取的页数，默认55页
        sleep_between: 分类之间的睡眠时间（秒），默认15秒
    """
    print(f"\n{'='*60}")
    print("开始自动爬取所有分类的微博热门数据")
    print(f"每个分类爬取 {count} 页，分类间间隔 {sleep_between} 秒")
    print(f"{'='*60}")
    
    success_count = 0
    failed_categories = []
    
    # 遍历所有分类
    for i, (category, _) in enumerate(tagDict.items(), 1):
        print(f"\n进度：{i}/{len(tagDict)} - 正在处理分类：{category}")
        
        try:
            success = get_weibo_hot(category, count)
            if success:
                success_count += 1
                print(f"✅ 分类 '{category}' 爬取成功")
            else:
                failed_categories.append(category)
                print(f"❌ 分类 '{category}' 爬取失败")
                
        except Exception as e:
            failed_categories.append(category)
            print(f"❌ 分类 '{category}' 爬取出错：{str(e)}")
        
        # 分类间睡眠（最后一个分类不需要睡眠）
        if i < len(tagDict):
            print(f"分类间睡眠 {sleep_between} 秒...")
            time.sleep(sleep_between)
    
    # 输出最终结果
    print(f"\n{'='*60}")
    print("所有分类爬取完成！")
    print(f"成功：{success_count}/{len(tagDict)} 个分类")
    if failed_categories:
        print(f"失败的分类：{', '.join(failed_categories)}")
    print(f"{'='*60}")


def crawl_specific_categories(categories: list, count: int = 55, sleep_between: int = 15):
    """
    爬取指定分类的微博热门数据
    
    Args:
        categories: 要爬取的分类列表
        count: 每个分类爬取的页数，默认55页
        sleep_between: 分类之间的睡眠时间（秒），默认15秒
    """
    print(f"\n{'='*60}")
    print(f"开始爬取指定分类的微博热门数据：{', '.join(categories)}")
    print(f"每个分类爬取 {count} 页，分类间间隔 {sleep_between} 秒")
    print(f"{'='*60}")
    
    success_count = 0
    failed_categories = []
    
    for i, category in enumerate(categories, 1):
        if category not in tagDict:
            print(f"❌ 分类 '{category}' 不存在，跳过")
            failed_categories.append(category)
            continue
            
        print(f"\n进度：{i}/{len(categories)} - 正在处理分类：{category}")
        
        try:
            success = get_weibo_hot(category, count)
            if success:
                success_count += 1
                print(f"✅ 分类 '{category}' 爬取成功")
            else:
                failed_categories.append(category)
                print(f"❌ 分类 '{category}' 爬取失败")
                
        except Exception as e:
            failed_categories.append(category)
            print(f"❌ 分类 '{category}' 爬取出错：{str(e)}")
        
        # 分类间睡眠（最后一个分类不需要睡眠）
        if i < len(categories):
            print(f"分类间睡眠 {sleep_between} 秒...")
            time.sleep(sleep_between)
    
    # 输出最终结果
    print(f"\n{'='*60}")
    print("指定分类爬取完成！")
    print(f"成功：{success_count}/{len(categories)} 个分类")
    if failed_categories:
        print(f"失败的分类：{', '.join(failed_categories)}")
    print(f"{'='*60}")


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description='微博热门数据爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 爬取所有分类（默认55页，间隔15秒）
  python crawl_weibo.py --all
  
  # 爬取所有分类，指定页数和间隔
  python crawl_weibo.py --all --pages 30 --sleep 10
  
  # 爬取指定分类
  python crawl_weibo.py --categories 搞笑 情感 明星
  
  # 爬取单个分类
  python crawl_weibo.py --single 房产
  
  # 查看所有可用分类
  python crawl_weibo.py --list-categories
  
  # 查看帮助
  python crawl_weibo.py --help
        """
    )
    
    # 创建互斥组，确保只能选择一种爬取方式
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '--all', '-a',
        action='store_true',
        help='爬取所有分类的微博热门数据'
    )
    
    group.add_argument(
        '--categories', '-c',
        nargs='+',
        metavar='CATEGORY',
        help='爬取指定分类的微博热门数据，可以指定多个分类'
    )
    
    group.add_argument(
        '--single', '-s',
        metavar='CATEGORY',
        help='爬取单个分类的微博热门数据'
    )
    
    group.add_argument(
        '--list-categories', '-l',
        action='store_true',
        help='列出所有可用的分类'
    )
    
    # 通用参数
    parser.add_argument(
        '--pages', '-p',
        type=int,
        default=55,
        help='每个分类爬取的页数（默认：55）'
    )
    
    parser.add_argument(
        '--sleep', '-t',
        type=int,
        default=15,
        help='分类之间的睡眠时间，单位秒（默认：15）'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='./weiboHot',
        help='输出目录（默认：./weiboHot）'
    )
    
    return parser.parse_args()


def list_available_categories():
    """
    列出所有可用的分类
    """
    print("\n可用的分类列表：")
    print("=" * 50)
    for i, (category, code) in enumerate(tagDict.items(), 1):
        print(f"{i:2d}. {category:<8} (代码: {code})")
    print("=" * 50)
    print(f"总计：{len(tagDict)} 个分类")


def validate_categories(categories):
    """
    验证分类名称是否有效
    
    Args:
        categories: 分类名称列表
        
    Returns:
        tuple: (有效分类列表, 无效分类列表)
    """
    valid_categories = []
    invalid_categories = []
    
    for category in categories:
        if category in tagDict:
            valid_categories.append(category)
        else:
            invalid_categories.append(category)
    
    return valid_categories, invalid_categories


if __name__ == "__main__":
    args = parse_arguments()
    
    # 如果请求列出分类，直接显示并退出
    if args.list_categories:
        list_available_categories()
        exit(0)
    
    # 更新输出目录
    if hasattr(args, 'output_dir'):
        os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("微博热门数据爬虫工具")
    print(f"输出目录：{args.output_dir}")
    print(f"每页爬取：{args.pages} 页")
    print(f"分类间隔：{args.sleep} 秒")
    print(f"{'='*60}")
    
    try:
        if args.all:
            # 爬取所有分类
            print("模式：爬取所有分类")
            crawl_all_categories(count=args.pages, sleep_between=args.sleep)
            
        elif args.categories:
            # 爬取指定分类
            print(f"模式：爬取指定分类 - {', '.join(args.categories)}")
            
            # 验证分类
            valid_cats, invalid_cats = validate_categories(args.categories)
            
            if invalid_cats:
                print(f"❌ 无效的分类：{', '.join(invalid_cats)}")
                print("请使用 --list-categories 查看所有可用分类")
                if not valid_cats:
                    print("没有有效的分类，程序退出")
                    exit(1)
                else:
                    print(f"将只爬取有效分类：{', '.join(valid_cats)}")
            
            if valid_cats:
                crawl_specific_categories(valid_cats, count=args.pages, sleep_between=args.sleep)
            
        elif args.single:
            # 爬取单个分类
            print(f"模式：爬取单个分类 - {args.single}")
            
            if args.single not in tagDict:
                print(f"❌ 分类 '{args.single}' 不存在")
                print("请使用 --list-categories 查看所有可用分类")
                exit(1)
            
            success = get_weibo_hot(args.single, args.pages)
            if success:
                print(f"✅ 分类 '{args.single}' 爬取成功")
            else:
                print(f"❌ 分类 '{args.single}' 爬取失败")
                exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断程序")
        print("程序已停止")
        exit(0)
    except Exception as e:
        print(f"\n❌ 程序执行出错：{str(e)}")
        exit(1)
    
    print("\n🎉 程序执行完成！")
```
