## maven的一些实践

### 打包时生成代码版本号和时间戳

* 使用```git-commit-id-plugin```插件，在```pom.xml```文件中添加插件配置：

  ```xml
  <!-- 生成代码仓库提交ID以及时间戳构建  -->
  <build>
      <plugins>
	      <plugin>
		      <groupId>pl.project13.maven</groupId>
			  <artifactId>git-commit-id-plugin</artifactId>
			  <version>2.2.4</version>
			  <executions>
			      <execution>
				      <goals>
					      <goal>revision</goal>
					  </goals>
				  </execution>
			  </executions>
			  <configuration>
			      <!-- 使properties扩展到整个maven bulid 周期
                  Ref: https://github.com/ktoso/maven-git-commit-id-plugin/issues/280 -->
				  <injectAllReactorProjects>true</injectAllReactorProjects>
				  <!--日期格式;默认值:dd.MM.yyyy '@' HH:mm:ss z;-->
				  <dateFormat>yyyyMMddHHmmss</dateFormat>
				  <!--,构建过程中,是否打印详细信息;默认值:false;-->
				  <verbose>true</verbose>
				  <!--是否生成"git.properties"文件;默认值:false;-->
				  <generateGitPropertiesFile>true</generateGitPropertiesFile>
				  <!-- ".git"文件路径;默认值:${project.basedir}/.git; ..表示上一级-->
				  <dotGitDirectory>${project.basedir}/.git</dotGitDirectory>
				  <gitDescribe>
				      <!--提交操作ID显式字符长度,最大值为:40;默认值:7;0代表特殊意义;-->
					  <abbrev>7</abbrev>
					  <!--构建触发时,代码有修改时(即"dirty state"),添加指定后缀;默认值:"";-->
					  <dirty>-dirty</dirty>
				  </gitDescribe>
			  </configuration>
		  </plugin>
	  </plugins>
	  <finalName>${name}-${git.commit.id.abbrev}-${git.build.time}</finalName>
  </build>
  ```

  如果只想要生成时间戳，可使用```build-helper-maven-plugin```：

  ```xml
  <!-- 只生成时间戳构建 -->
  <build>
      <plugins>
	      <plugin>
		      <groupId>org.codehaus.mojo</groupId>
			  <artifactId>build-helper-maven-plugin</artifactId>
			  <version>3.0.0</version>
			  <executions>
			      <execution>
				      <id>timestamp-property</id>
					  <goals>
					      <goal>timestamp-property</goal>
					  </goals>
				  </execution>
			  </executions>
			  <configuration>
			      <name>current.time</name>
				  <pattern>yyyyMMddHHmmss</pattern>
				  <timeZone>GMT+8</timeZone>
				  <fileSet/>
				  <regex/>
				  <source/>
				  <value/>
			  </configuration>
		  </plugin>
	  </plugins>
	  <finalName>${name}-${current.time}</finalName>
  </build>
  ```

### 引入本地jar包

* 在项目根目录新增```lib```文件夹，将本地jar包放入该文件夹。

* 在```pom.xml```文件中添加依赖：

  ```xml
  <dependency>
      <groupId>com.example</groupId>
      <artifactId>local-jar</artifactId>
      <version>1.0-SNAPSHOT</version>
      <scope>system</scope>
      <systemPath>${project.basedir}/lib/local-jar-1.0-SNAPSHOT.jar</systemPath>
  </dependency>
  ```

  其中```scope```属性设置为```system```，表示该依赖是系统路径，```systemPath```属性设置为本地jar包的路径。

* ```springboot```打包时，需添加```resource```配置：
  
  ```xml
  <resources>
      <resource>
	      <directory>${project.basedir}/lib</directory>
		  <targetPath>BOOT-INF/lib/</targetPath>
		  <includes>
		      <include>*.jar</include>
		  </includes>
      </resource>
  </resources>
  ```
  

### 参考文献

* [Maven打包使用代码版本号和时间戳](https://qinguan.github.io/2018/03/11/maven-package-with-version-and-timestamp/)
* [maven引入本地jar包的方法](https://cloud.tencent.com/developer/article/1510883)