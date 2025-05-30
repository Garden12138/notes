## mybatis的一些实践

### 批量插入

* ```for```循环单条插入：

   ```mapper.xml```代码：

   ```xml
   <insert id="insertOne">
   insert into tb_student
        (name,age)
    values
        (#{student.name},#{student.age})
   </insert>
   ```

   ```java```代码：

   ```java
   for(int i = 0; i < insertList.size(); i++) {
       mapper.insertOne(insertList.get(i));
   }
   ```

   实际上每次```mapper```方法调用都会进行一次连接数据库、预处理（```PreparedStatement```）、```execute```（执行```SQL```）等过程，效率低，不推荐使用。

* ```foreach```循环构建多个参数值插入：

  ```mapper.xml```代码：

  ```xml
  <insert id="insertBatch">
    insert into tb_student
        (name,age)
    values
    <foreach collection="students" item="student" separator=",">
        (#{student.name},#{student.age})
    </foreach>
  </insert>      
  ```

  这种方式是通过多个```PreparedStatement```来批量插入，效率高，推荐使用。但数据量过大时，由于拼接的```SQL```过长，可能会导致````IO```异常，建议在此基础上分批插入：

  ```java
  // 批量插入的最大数量
  private static final int maxInsertItemNumPerTime = 500;

  // 批量插入抽象方法，list为待插入数据集，insertFunc为插入方法（即```mapper```方法）
  public <T> void batchSplitInsert(List<T> list, Consumer insertFunc) {
      List<List<T>> all = new ArrayList<>();
      if (list.size() > maxInsertItemNumPerTime) {
          int i = 0;
          while (i < list.size()) {
              if (i + maxInsertItemNumPerTime > list.size()){
                  subList = list.subList(i, list.size());
              } else {
                  subList = list.subList(i, i + maxInsertItemNumPerTime);
              }
              i = i + maxInsertItemNumPerTime;
              all.add(subList);
          }
          all.parallelStream().forEach(insertFunc);
      } else {
          insertFunc.accept(list);
      }
  }
  ```

  实际调用：

  ```java
  // 待插入数据集
  List<Student> students = getStudents();
  Consumer<List<Student>> consumer = o -> mapper.insertBatch(o);
  batchSplitInsert(students, consumer);
  ```       

* ```mybatis dynamic```的多行插入支持：

  ```java
  try (SqlSession session = sqlSessionFactory.openSession()) {
      // 1. 获取Mapper实例
      GeneratedAlwaysAnnotatedMapper mapper = session.getMapper(GeneratedAlwaysAnnotatedMapper.class);
    
      // 2. 准备数据
      List<GeneratedAlwaysRecord> records = getRecordsToInsert();
    
      // 3. 构建批量插入语句（核心部分）
      MultiRowInsertStatementProvider<GeneratedAlwaysRecord> multiRowInsert = insertMultiple(records)
          .into(generatedAlways)                  // 3.1 指定目标表
          .map(id).toProperty("id")               // 3.2 列-属性映射
          .map(firstName).toProperty("firstName")
          .map(lastName).toProperty("lastName")
          .build()                                // 3.3 构建语句
          .render(RenderingStrategies.MYBATIS3);  // 3.4 渲染为MyBatis可执行SQL
    
      // 4. 执行批量插入
     int rows = mapper.insertMultiple(multiRowInsert);
  }
  ```

  ```java
  public interface GeneratedAlwaysAnnotatedMapper {
      @InsertProvider(type = SqlProviderAdapter.class, method = "insertMultiple")
      int insertMultiple(MultiRowInsertStatementProvider<GeneratedAlwaysRecord> provider);
  }
  ```

  ```java
  public final class GeneratedAlways {
      public static final GeneratedAlwaysTable table = new GeneratedAlwaysTable();
    
      public static final class GeneratedAlwaysTable extends SqlTable {
          public final SqlColumn<Integer> id = column("id", JDBCType.INTEGER);
          public final SqlColumn<String> firstName = column("first_name", JDBCType.VARCHAR);
          public final SqlColumn<String> lastName = column("last_name", JDBCType.VARCHAR);
          // 构造函数...
      }
  }
  ```
  
  需要依赖：

  ```xml
  <dependency>
      <groupId>org.mybatis.dynamic-sql</groupId>
      <artifactId>mybatis-dynamic-sql</artifactId>
      <version>1.4.0</version>
  </dependency>
  ```

  这种方式底层生成的```SQL```也是多个参数值形式，与方法二一致，但从实现方式来讲，方法二更加简洁，推荐使用。

### 参考文献

* [使用Mybatis批量插入大量数据的实践](https://segmentfault.com/a/1190000041216368)
* [MyBatis Dynamic SQL Insert Statements](https://mybatis.org/mybatis-dynamic-sql/docs/insert.html)