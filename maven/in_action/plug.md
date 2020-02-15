## Maven in action
#### 插件
> 插件
  * 插件目标
    * 对于插件本身，为了能够完成多个任务实现了多个功能，这些功能聚集在一个插件里，每个功能就是一个插件目标。
    * 插件目标的表示方式为插件前缀名:插件目标，如dependency:analyze，dependency:tree，dependency:list为maven-dependency-plugin插件的多个目标。
  * 插件绑定
    * Maven的生命周期的阶段与插件互相绑定，用以完成实际的构建任务。例如项目编译任务，对应default生命周期的compile这阶段，maven-compiler-plugin这一插件的compile目标能够完成该任务。
      ![Snipaste_2020-02-15_18-35-30.png](https://i.loli.net/2020/02/15/wsYalUr6W1kCRuq.png)
  * 内置绑定
  * 自定义绑定
  * 插件配置
  * 获取插件信息
  * 从命令行调用插件
  * 插件解析机制