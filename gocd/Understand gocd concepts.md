## 理解 gocd 概念

> Task【任务】

* 任务或构建任务是需要执行的最小操作，通常它是一条单体命令：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_16-25-16.png)

> Job【作业】

* 一个作业由多个任务组成，作业中的多个任务串行执行，若其中一个任务失败，后续任务将不会执行并且该作业将视为失败。作业中的每个任务都作为一个独立的程序运行，故任务对其任何环境变量所做的更改都不会影响后续任务，但对文件系统的任何更改都将对后续任务可见：
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_16-59-55.png)  

> Stage【阶段】

* 一个阶段由多个作业组成，阶段中的多个作业并行执行，每个作业都独立于其他作业运行，若其中一个作业失败，该阶段将视为失败但其他作业不受影响将继续运行完成：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-02-54.png)

> Pipeline【管道】

* 一个管道由多个阶段组成，管道中的多个阶段串行执行，若其中一个阶段失败，后续阶段将不会执行并且该管道将视为失败：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-03-04.png) 

> Materials【材料】

* 材料是管道运行的因素。通常它是源代码存储库，如```Git```、```SVN```以及```Mercurial```等。```GoCD```服务器会不断轮询其对应配置的材料，当发现新的更高或提交时，将运行或触发相应的管道。存在不同类型的材料，如```Git```与```SVN```分别为：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-03-30.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-03-38.png)

  管道可以配置多种材料，如同时配置```Git```与```SVN```材料，当任意存储库有新提交时，将触发管道：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-07-33.png)

  存在特殊的材料-定时触发器，可以在指定时间或指定时间间隔触发管道：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-11_17-03-46.png)

> Pipeline Dependencies

> Fan-in and Fan-out

> Value Stream Map

> Artifacts

> Agent

> Resources

> Environment

> Environment Variables

> Templates

> 参考文献

* [Concepts in GoCD](https://docs.gocd.org/current/introduction/concepts_in_go.html)