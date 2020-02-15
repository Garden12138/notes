## Maven in action
#### 生命周期
> 生命周期
  * 何为生命周期
    * 在Maven日常使用中，命令行的输入对应Maven生命周期，如mvn package表示执行默认生命周期的package阶段。Maven生命周期是抽象的，实际行为由插件实现，如上述的package阶段由插件maven-jar-plugin完成。Maven生命周期是对所有构件过程进行抽象和统一，Maven从大量项目和构建工具中学习反思后总结的一套高度完善，易扩展的生命周期，其中包括项目的清理，初始化，编译，测试，打包，集成测试，验证，部署和站点生成等几乎所有的构建步骤，所有的构建过程都映射到生命周期上。
  * 生命周期详解
    * Maven拥有三套相互独立的生命周期，分别为清理项目的clean生命周期，构建项目的default生命周期，建立项目站点的site生命周期。每个生命周期都包含阶段（phase），每个阶段都是有序的并且前后存在依赖关系（假设阶段为a->b->c，执行阶段c时会依次先执行a，b阶段）。
    * clean生命周期，目的为清理项目。
      * pre-clean，执行一些清理前需要完成的工作。
      * clean，清理上次构建生成的文件。
      * post-clean，执行一些清理后需要完成的工作。
    * default生命周期，定义了真正构建时所需要执行的所有步骤。
      * vaildate，验证项目是正确的，所有必要信息都是可用的。
      * initialize，初始化构建状态，例如设置属性或创建目录。
      * generate-sources，生成包含在编译中的任何源代码。
      * process-sources，处理源代码，例如过滤任何值。
      * generate-resources，生成包含在包中的资源。
      * process-resources，将资源复制并处理到目标目录中，准备打包。
      * compile，编译项目源代码。
      * process-classes，从编译后生成生成的文件，例如在Java类上执行字节码增强。
      * generate-test-sources，生成包含在编译中的任何测试源代码。
      * process-test-sources，处理测试源代码，例如过滤任何值。
      * generate-test-resources，为测试创建资源。
      * process-test-resources，将资源复制并处理到测试目标目录中。
      * test-compile，将测试源代码编译到测试目标目录。
      * process-test-classes，从测试编译后post-process生成文件，例如在Java类上执行字节码增强。对于Maven2.0.5和以上。
      * test，使用合适的单元测试框架运行测试。
      * prepare-package，在实际包装前执行必要的准备工作。
      * package，使用已编译的代码，并将其打包成可部署格式，例如JAR。
      * pre-integration-test，执行集成测试之前需要执行的操作。
      * integration-test，在需要集成测试的环境中，处理并部署包。
      * post-integration-test，执行集成测试后所需要的操作，例如清理环境。
      * verify，运行任何检查以验证包是否有效，并满足质量标准。
      * install，将该包安装到本地存储中，作为本地其他项目的依赖项。
      * deploy，在集成或发布环境中完成，将最终包复制到远程存储库中，以便与其他开发人员和项目共享。
    * site生命周期，目的为建立和发布项目站点。
      * pre-site，执行一些在生成项目站点之前需要完成的工作。
      * site，生成项目站点文档。
      * post-site，执行一些在生成项目站点之后需要完成的工作。
      * site-deploy，将生成的项目站点发布到服务器上。
  * 命令行与生命周期
    * 命令行执行的任务最主要方式是调用Maven生命周期阶段。每个生命周期都是相互独立的，一个生命周期的阶段存在前后依赖关系。
    * mvn clean，调用clean生命周期的clean阶段。
    * mvn test，调用default生命周期的test阶段。
    * mvn clean install，调用clean生命周期的clean阶段和default生命周期的install阶段。
    * mvn clean deploy site-deploy，调用clean生命周期的clean阶段，default生命周期的deploy阶段以及site生命周期的site-deploy。