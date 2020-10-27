## Stream与Lambda实践

> Stream简介
  * Stream广义上为java.util.stream包中诸多类，集合类中常转换为Stream并以流方式对集合元素进行加工处理，降低编程难度，其中最核心的是interface Stream。
    
    ![StreamUML.png](https://i.loli.net/2020/10/26/wr3QIfR9H6vG8Sp.png)

    Stream继承BaseStream，其中Stream中定义了一些实用的方法，如filter，map，collect，forEach。
  * Stream的创建
    ```
    /**
     * 根据集合类.stream()方法获取Stream对象
     * @param collection
     * @return
     */
    public static<T> Stream<T> getStream(Collection<T> collection){
        return collection.stream();
    }

    /**
     * 根据Stream.of()方法获取Stream对象
     * @param elements
     * @return
     */
    public static<T> Stream<T> getStream(T... elements) {
        return Stream.of(elements);
    }

    /**
     * 根据集合类.stream()方法获取Stream多线程对象
     * @param collection
     * @return
     */
    public static<T> Stream<T> getParallelStream(Collection<T> collection){
        return collection.parallelStream();
    }

    /**
     * 测试方法
     * @param args
     */
    public static void main(String[] args) {
        Stream<String> stream1 = StreamFactory.getStream(
                Arrays.asList(new String[]{"s1","s2","s3"}));
        Stream<String> stream2 = StreamFactory.getStream(
                "s1","s2","s3");
        System.err.println(stream1 == stream2);
        Stream<String> parallelStream = StreamFactory.getParallelStream(
                Arrays.asList(new String[]{"s1","s2","s3"}));
        parallelStream.forEach(element -> {
            System.err.println(Thread.currentThread().getName() + ">>>" + element);
        });
    }
    ```
    上述方法由自定义工厂类StreamFactory实现。

  * Stream的基础操作
    * Stream的基础操作可分为两种，一种为中间操作，即对流式数据操作，操作结果返回Stream；另一种为终止操作，即对流式数据封装操作，操作结果返回Stream操作定义的返回类型。
    * Matching
      ```
      //判断集合内是否任意元素符合断言条件 => boolean anyMatch(Predicate<? super T> predicate);

      Arrays.asList("s1", "s3").stream().anyMatch(element -> element.contains("s1"));

      true

      //判断集合内是否全部元素符合断言条件 => boolean allMatch(Predicate<? super T> predicate);

      Arrays.asList("s1", "s1").stream().allMatch(element -> element.contains("s1"));

      true

      //判断集合内是否没有元素符合断言条件 => boolean noneMatch(Predicate<? super T> predicate);

      Arrays.asList("s2", "s3").stream().noneMatch(element -> element.contains("s1"));

      true
      ```
    * Filtering
      ```
      //根据断言条件过滤集合数据流 => Stream<T> filter(Predicate<? super T> predicate);

      Arrays.asList("s1", "s2").stream().filter(element -> element.contains("s1")).collect(Collectors.toList());

      [s1]
      ```
    * Mapping
      ```
      //加工Stream中的值，将加工后的值以新的Stream返回 => <R> Stream<R> map(Function<? super T, ? extends R> mapper);

      Arrays.asList("s1", "s2").stream().map(element -> {return element + "-map";}).collect(Collectors.toList());

      [s1-map, s2-map]
      ```
    * FlatMap
    * Reduction
    * Collecting

> 内置函数式接口的分类与使用

> Lambda表达式实践

> Stream实践