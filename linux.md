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
-l use a long listing format
-t sort by modification time, newest first
```

> 文本处理

> 压缩

> 日常运维

> 系统状态概览

> 工作常用

> PS
```
## 查看命令用法
order --help
example: ls --help
```