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
```
## 打印csv文件的第一列以及第二列
awk -F "," '{print $1,$2}' test.csv
## 查看网络连接所处于的网络状态
netstat -ant | awk 'BEGIN{print "State","Count"} /^tcp/ {rt[${6}]++} END{ for(i in rt){print i,rt[i]} }
## 输出Recv-Q不为0的记录
netstat -ant | awk '$2 > 0 {print}'
## 查看外网连接数，根据IP分组
netstat -ant | awk '/^tcp/ {print $4}' | awk -F ":" '!/^:/ {print $1}' |sort | uniq -c'
## 以逗号,冒号:分隔符打印test.txt文件的第一列以及第二列并以符号-分割输出 
awk 'BEGIN{FS="[,:]";OFS="-"} {print$1,$}' test.txt
## 以逗号分割打印test.txt文件第三列内容
awk 'BEGIN {FS=','} if(NF == 3){print}' test.txt
## 打印test.txt文件并显示行号
awk '{print NR,$0}' text.txt
## options
-F field separator
$1 first field,$0 deputy original string
FS field separator
OFS output field separator
NF field number
NR line number
```
```
## 打印第五行test.log内容
sed -n '5 p' test.log
## 打印第一行至第五行test.log内容
sed -n '1,5 p' test.log
sed -n '1,+4 p' test.log
## 打印第一行至最后一行test.log内容
sed -n '1,$ p' test.log
## 打印奇数行test.log内容
sed -n '1~2 p' test.log
## 打印偶数行test.log内容
sed -n '2~2 p' test.log
## 打印以2019开头至出现api字样之间行的test.log内容
sed -n '/^2019/,/api/ p' test.log
## 打印长度不少于100字符的test.log行内容
sed -n '^.{50} p' test.log
## 统计test.log每个单词出现的次数
sed 's/ /\n/g' test.log | sort | uniq -c 
## options
-n suppress automatic printing of pattern space
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
```
## 删除text.log第一行至第五行内容
sed '1,5 d' text.log
## 输出text.log第一行至第五行内容到text_bk.log文件
sed -n '1,5 w text_bk.log' text.log
## 删除text.log所有以#开头的行以及空行
sed -e 's/#.*//' -e '/^$/ d' text.log
## 将2019开头至出现api字样之间行的test.log内容的a字符或者b字符或者c字符替换为d字符
sed -n '/^2019/,/api/ s/[a,b,c]/d/g' test.log
## 将text.log的每一行使用""引号
sed -n 's/.*/"$"/' test.log
## options
-n
-e
```

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
## 查看系统环境变量
env
```
```
## 设置jdk环境变量
export PATH=$PATH:/usr/java/jdk1.8.0_152/bin
```
```
## 删除当前目录下的所有.class文件
find . | grep '.class$' | xargs rm -rvf 
## 将当前目录下的rmvb文件移动至/usr/local目录
ls *.rmvb | xagrs -nl -i cp {} /usr/local
## options
-n use at most MAX-ARGS arguments per command line
-l Use at most MAX-LINES nonblank input lines per command line
-i Replace R in initial arguments with names read from standard input. If R is unspecified, assume {}
```
```
## 显示系统当前时间
date
```
```
## 显示bash命令的二进制程序地址
whereis -b bash
## 显示bash命令的帮助文档地址
whereis -m bash
## options
-b search only for binaries
-m search only for manuals
```
```
## 每天凌晨0点重启SSH服务
0 0 * * * /sbin/service sshd restart 
```
```
## 将scp.txt文件传输至39.108.168.201的/tmp目录下
scp scp.txt root@39.108.168.201:/tmp
## 将scp.txt文件覆盖至39.108.168.201的/tmp/scp.txt
scp scp.txt root@39.108.168.201:/tmp/scp.txt
```
```
## 远程登录主机39.108.168.201
ssh -v -p 22 root@39.108.168.201
## options
-v detailed output process
-p specified port
```
```
## 使用断点续传方式下载百度首页并且命名为baidu.html
wget -o baidu.html -c http://www.baidu.com/index.html
## 使用后台方式下载百度首页并且命名为baidu.html
wget -o baidu.html -b http://www.baidu.com/index.html
## options
-o write documents to file
-c resume getting a partially-downloaded file
-b go to background after startup
```
```
## 对https://www.example.com发出GET请求
curl https://www.example.com
## 对https://www.example.com发出POST请求
curl -X POST https://www.example.com
```
```
## 使用root用户登录39.108.168.201数据库服务器
mysql -u root -p -h 39.108.168.201
```
```
## 查看CPU占用最高的java线程
top
shift + p
top -Hp pid
printf 0x%x pid
whereis java
cd ../bin
jstack pid
```

> PS
  * 查看命令用法 
    ```
    order --help
    example: ls --help
    ```
  * [菜鸟教程](https://www.runoob.com/linux/linux-command-manual.html)
