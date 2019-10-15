## 常用命令

> 目录/文件操作

```
## 创建目录以及父目录a/b/c/d 
mkdir -p a/b/c/d
## options 
-p no error if existing, make parent directories as needed
```
```
## 拷贝文件夹a到/tmp目录
cp -rvf a/ /tmp/
## options
-r copy directories recursively
-v explain what is being done
-f if an existing destination file cannot be opened, remove it and try again (this option is ignored when the -n option is also used)
```
```
## 移动文件夹a到/tmp目录，并重命名b
mv -vf a /tmp/b
## options
-v explain what is being done
-f do not prompt before overwriting
```
```
## 删除当前路径文件b
rm -rvf b
## options
-r remove directories and their contents recursively
-v explain what is being done
-f ignore nonexistent files and arguments, never prompt
```
> 漫游
```
## 查看/var目录下的文件详细信息并按最新创建时间显示
ls -lt /var
## options
-l use a long listing format
-t sort by modification time, newest first
```
```
## 查看当前终端所在目录
pwd
```
```
## 切换至/var目录
cd /var
```
```
## 查找当前目录下所有以abc开头并且不含.md扩展名的具有0777权限的文件
find . -type -f -iname "abc*" ! -iname "*.md" -perm 0777
## options
-type set search result type
-iname set ignore case search name
-perm set search permission
```

> 查看文件
```
## 查看cat.log文件内容并显示行数
cat -n cat.log
## options
-n number all output lines
```
```
## 查看less.log文件，并匹配less内容
cat less.log
/less
## options
e move next line
y move last line
f move next screen
b move last screen
n search the next matching text
N search the last matching text
g jump the first line
G jump the last line
## 查看历史命令
history | less
```
```
## 滚动查看tail.log日志
tail -f tail.log
## 查看tail.log后100行日志内容
tail -n100 tail.log
## 查看tail.log前100行日志内容
head -n100 tail.log
## options
-f output appended data as the file grows
-n output the last K lines, instead of the last 10
```

> 过滤
```
## 查看grep.log日志关键字grep的前10行与后10行内容
grep -rn 'grep' -A10 -B10 grep.log
-r like --directories=recurse
-n print line number with output lines
-A after maching text n line 
-B before maching text n line
```

> 文本处理

> 压缩
```
## 压缩tartest.c文件
tar -czvf tartest.tar tartest.c
## 查看tartest.tar文件信息
tar -tzvf tartest.tar
## 解压tartest.tar文件
tar -xzvf tartest.tar
## options
-c create a new archive
-t list the contents of an archive
-x extract files from an archive
-z filter the archive through gzip
-v verbosely list files processed
-f use archive file or device archive
```

> 日常运维

```
## 立即关机停机
shutdown -h now
## 立即关机并重新开机
shutdown -r now
## 5分钟后关机并提示
shutdown +5 "System will shutdown after 5 minutes"
## options
-h power-off the machine,halt the machine 
-r reboot the machine
```
```
## mount
```
```
## chmod
```
```
## su
```
```
## yum
```
```
## password
```
```
## service
```
```
## systemctl
```
> 系统状态概览

> 工作常用

> PS
  * 查看命令用法 
    ```
    order --help
    example: ls --help
    ```
  * [菜鸟教程](https://www.runoob.com/linux/linux-command-manual.html)
