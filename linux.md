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
## 将/dev/SSD1用唯读模式挂在/mnt目录下
mount -o ro /dev/SSD1 /mnt
## 将/tmp/image.iso这个光碟的image档使用loop模式挂在/mnt/cdrom目录下
mount -o loop /tmp/image /mnt/cdrom
## options
-o ro use only read mode
-o loop use loop mode to split a file as a hard disk and hang it on the system
```
```
## 将chown.txt文件设置所属用户以及用户组为garden，gardengroup
chown garden:gardengroup chown.txt
## 将当前目录下的所有文件及其子文件设置所属用户以及用户组为garden，gardengroup
chown -R garden:gradengroup *
## options
-R operate on files and directories recursively
``` 
```
## 将chmod.txt文件设置为所有人皆可读取
chmod ugo+r chmod.txt
chmod a+r chmod.txt
## 将chmod.txt文件设置为所有人皆可写入
chmod ugo+w chmod.txt
chmod a+w chmod.txt
## 将chmod.txt文件设置为所有人皆可执行
chmod ugo+x chmod.txt
chmod a+x chmod.txt
## 将chmod.txt文件设置为所有人皆可读写执行
chmod ugo=rwx chmod.txt
chmod a=rwx chmod.txt
chmod 777 chmod.txt
## 将文件 chmod1.txt与chmod2.txt设为该文件拥有者与其所属同一个群体者可写入，但其他以外的人则不可写入
chmod ug+w,o-w  chmod1.txt chmod2.txt
## 将目前目录下的所有文件与子目录皆设为任何人可读取
chmod -R a+r *
## options
u user
g group of user
o other user
a all user
+ add perm
- cancel perm
= give perm
r read-perm,4
w write-perm,2
x run-perm,1
-R change files and directories recursively
```
```
## 切换至garden用户
su - garden
```
```
## 下载wget命令
yum install wget -y
-y  answer yes for all questions
```
```
## 修改garden用户密码
passwd garden
## 显示garden账号密码信息
passwd -S garden
## options
-S report password status on the named account (root only)
```
```
## 重启mysql服务
service mysql restart
systemctl restart mysqld
```

> 系统状态概览
```
## 查看java进程
ps -ef | grep java
```
```
## 查看所有进程的CPU以及内存使用率
top -c
## 查看233进程的CPU以及内存使用率
top -p 233
## options
-c complete command
-p pid
```
```
## 查看系统内存使用情况
free -t
## options
-t show total for RAM + swap
```
```
## 查看系统磁盘使用情况
df -h
## options
-h print sizes in human readable format (e.g., 1K 234M 2G)
```
```
## 查看系统网络配置信息
ifconfig
```
```
## 查看系统当前内核信息
uname -a
## options
-a print all information
```
```
## 查看当前操作系统是否与百度相连通
ping www.baidu.com
```
```
## 查看当前系统的所有tcp连接
netstat -anpt
## 查看当前系统的所有udp连接
netstat -anpu
##
-a display all sockets
-n don't resolve names 
-t tcp protocol
-p display PID/Program name for sockets
-u udp protocol
```

> 工作常用
```
## export
```
```
## xargs
```
```
## date
```
```
## whereis
```
```
## crontab
```
```
## scp
```
```
ssh
```
```
wget
```
```
mysql
```

> PS
  * 查看命令用法 
    ```
    order --help
    example: ls --help
    ```
  * [菜鸟教程](https://www.runoob.com/linux/linux-command-manual.html)
