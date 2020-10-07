## 对象拷贝方式实践

> 使用Spring的BeanUtils
  * 引入依赖（SpringBoot项目自带）
  * 使用示例
    ```
    public List<TestVo> springBeanUtils(List<TestEntity> testEntityList) {
        long beginTime = System.currentTimeMillis();
        List<TestVo> testVoList = new ArrayList<>();
        testEntityList.forEach(testEntity -> {
            TestVo testVo = new TestVo();
            org.springframework.beans.BeanUtils.copyProperties(testEntity,testVo);
            testVoList.add(testVo);
        });
        long endTime = System.currentTimeMillis();
        log.info("{}条数据，花费时间/ms：{}",testVoList.size(),(endTime - beginTime));
        return testVoList;
    }
    ```

> 使用Apache的BeanUtils
  * 引入依赖
    ```
    <!-- Apache的BeanUtils依赖 -->
	<dependency>
        <groupId>commons-beanutils</groupId>
		<artifactId>commons-beanutils</artifactId>
		<version>1.8.3</version>
	</dependency>
    ```
  * 使用示例
    ```
    public List<TestVo> apacheBeanUtils(List<TestEntity> testEntityList) {
        long beginTime = System.currentTimeMillis();
        List<TestVo> testVoList = new ArrayList<>();
        testEntityList.forEach(testEntity -> {
            TestVo testVo = new TestVo();
            try {
                org.apache.commons.beanutils.BeanUtils.copyProperties(testEntity,testVo);
            } catch (IllegalAccessException e) {
                e.printStackTrace();
            } catch (InvocationTargetException e) {
                e.printStackTrace();
            }
            testVoList.add(testVo);
        });
        long endTime = System.currentTimeMillis();
        log.info("{}条数据，花费时间/ms：{}",testVoList.size(),(endTime - beginTime));
        return testVoList;
    }
    ```

> 使用MapStruct
  * 引入依赖
    ```
    <!-- MapStruct依赖 -->
	<dependency>
        <groupId>org.mapstruct</groupId>
		<artifactId>mapstruct-jdk8</artifactId>
		<version>1.2.0.Final</version>
	</dependency>
	<dependency>
		<groupId>org.mapstruct</groupId>
		<artifactId>mapstruct-processor</artifactId>
		<version>1.2.0.Final</version>
	</dependency>
    ```
  * 使用示例
    ```
    public List<TestVo> mapStruct(List<TestEntity> testEntityList) {
        long beginTime = System.currentTimeMillis();
        List<TestVo> testVoList = Mappers.getMapper(TestTransfer.class).entityToVo(testEntityList);
        long endTime = System.currentTimeMillis();
        log.info("{}条数据，花费时间/ms：{}",testVoList.size(),(endTime - beginTime));
        return testVoList;
    }
    //拷贝接口
    @Mapper
    public interface TestTransfer {
        List<TestVo> entityToVo (List<TestEntity> testEntityList);
    }
    ```
  * 原理

    MapStruct使用注解处理器于编译时期生成实现类，实现类内容原生new对象后进行setter/getter方式进行属性值拷贝。
    ```
    //
    // Source code recreated from a .class file by IntelliJ IDEA
    // (powered by Fernflower decompiler)
    //
    package com.garden.transfer;
    import com.garden.entity.TestEntity;
    import com.garden.vo.TestVo;
    import java.util.ArrayList;
    import java.util.Iterator;
    import java.util.List;
    public class TestTransferImpl implements TestTransfer {
        public TestTransferImpl() {}
        
        public List<TestVo> entityToVo(List<TestEntity> testEntityList) {
            if (testEntityList == null) {
                return null;
            } else {
                List<TestVo> list = new ArrayList(testEntityList.size());
                Iterator var3 = testEntityList.iterator();
                while(var3.hasNext()) {
                    TestEntity testEntity = (TestEntity)var3.next();
                    list.add(this.testEntityToTestVo(testEntity));
                }
            return list;
            }
        }
        
        protected TestVo testEntityToTestVo(TestEntity testEntity) {
            if (testEntity == null) {
                return null;
            } else {
                TestVo testVo = new TestVo();
                testVo.setId(testEntity.getId());
                testVo.setName(testEntity.getName());
                testVo.setNumber(testEntity.getNumber());
                return testVo;
            }
        }
    }
    ```

> 多种对象拷贝方式的耗时对比

  | 数据规模\技术选型 | Spring | Apache | MapStruct |
  | :--- | :--- | :--- | :--- |
  | 10w | 90ms | 739ms | 11ms |
  | 100w | 421ms | 3835ms | 48ms |


> 小结
  * 通过这次简单的实践对比，掌握多种对象拷贝方式以及耗时性能方面的差异，一般分页且字段灵活多变的业务场景需求下，Spring与MapStruct差别不大，建议使用Spring的对象拷贝方式。对于全量且字段固定的业务场景需求下，建议使用MapStruct的对象拷贝方式。Apache的对象拷贝方式耗时与其余两者差距较大，一般不考虑使用。

> 参考文献
  * [你还在用BeanUtils做对象拷贝吗](https://juejin.im/post/6847902222572126222)

> 示例代码
  * [码云](https://gitee.com/FSDGarden/springboot/tree/object-copy)