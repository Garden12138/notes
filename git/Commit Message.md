## Git Commit Message

> 优雅的提交方式
  * 提交信息与业务相关
    
    提交信息内容能充分体现实现的功能或模块，也可直接使用需求描述作为提交信息。

    ```
    使用
    git commit -m"实现单点登陆接口"
    替代
    git commit -m"实现新功能"
    ```

  * 提交信息中写明类型
    
    提交类型根据提交原因可进行分类：新功能，代码升级或变更，Bug修复，文档编写，主题UI变更和测试用例。
    * Feat：新功能
    * Upgrade：代码升级或变更
    * Fix：Bug修复
    * Doc：文档或README编写
    * Style：主题UI变更
    * Test：测试用例

    ```
    使用
    git commit -m"Feat：实现单点登陆接口"
    替代
    git commit -m"实现单点登陆接口"
    ```

  * 提交信息内容尽量简短
    
    在能够准确表达本次提交所代表含义的情况下，字数尽量少，最好不超过50个字符。

    ```
    使用
    git commit -m"Feat：实现单点登陆接口"
    替代
    git commit -m"Feat：实现单点登陆接口，并修改了Login.java...（后续100个字符）"
    ```

  * 必要时要写描述
    
    必要时对提交信息进行补充说明或详细描述，比如对于冲突文件的详细描述。

    ```
    使用
    git commit -m"Upgrade: Update meta
    * update contributors
    * update webpack
    "
    替代
    git commit -m"Upgrade: Update meta"
    ```

  * 尽量使用英文
    
    提交信息尽量使用英文，语句的首字母使用大写字符，语句的结尾不要有句号(.)

> 小结
  * 养成良好的提交习惯，方便个人以及团队的阅读交流。