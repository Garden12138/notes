#!/usr/bin/python3

import urllib.request
import urllib.parse
import ssl

ssl._create_default_https_context = ssl._create_stdlib_context

url200 = 'http://www.baidu.com/'
url404 = 'http://www.baidu.com/404'

try:
    response = urllib.request.urlopen(url404)
    print("Status:", response.getcode())
    print("ResponseBody:", repr(response.read(100)))
except urllib.error.HTTPError as e:
    print('HTTPError:%d, Reason:%s'% (e.code, e.reason))

encoded_url = urllib.request.quote(url404)
print("EncodedUrl:", encoded_url)
decoded_url = urllib.request.unquote(encoded_url)
print("DecodedUrl:", decoded_url)

url = 'https://www.runoob.com/?s='
keyword = 'Python 教程'
key_code = urllib.request.quote(keyword)
url_all = url+key_code
header = {
    'User-Agent':'Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}
#data = urllib.parse.urlencode({'name': 'runoob', 'age': 25}).encode('utf-8')
# request = urllib.request.Request(url_all, data=data, headers=header)
request = urllib.request.Request(url_all, headers=header)
reponse = urllib.request.urlopen(request).read(100)
print(reponse)

url_parse = urllib.parse.urlparse("https://www.runoob.com/?s=python+%E6%95%99%E7%A8%8B")
print(url_parse)