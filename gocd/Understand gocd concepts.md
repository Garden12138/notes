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

> Materials

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