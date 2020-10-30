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
      ```
      //先将层级关系铺平,再加工最低层级Stream中的值，最后将加工后的值以新的Stream返回 => <R> Stream<R> flatMap(Function<? super T, ? extends Stream<? extends R>> mapper);

      BookCase bookCaseA = new BookCase("bookCaseA");
      List<String> bookCaseABooks = new ArrayList<>();
      bookCaseABooks.add("book-1");
      bookCaseABooks.add("book-2");
      bookCaseA.setBooks(bookCaseABooks);
      BookCase bookCaseB = new BookCase("bookCaseB");
      List<String> bookCaseBBooks = new ArrayList<>();
      bookCaseBBooks.add("book-3");
      bookCaseBBooks.add("book-4");
      bookCaseB.setBooks(bookCaseBBooks);
      List<BookCase> bookCases = new ArrayList<>();
      bookCases.add(bookCaseA);
      bookCases.add(bookCaseB);
      bookCases.flatMap(bookCases,object -> {
            BookCase bookCase = (BookCase) object;
            List<String> newBooks = new ArrayList<>();
            for (String book : bookCase.getBooks()) {
                book += " new!";
                newBooks.add(book);
            }
            bookCase.setBooks(newBooks);
            return bookCase.getBooks().stream();
      }).collect(Collectors.toList());

      [book-1 new!, book-2 new!, book-3 new!, book-4 new!]
      ```
    * Reduction
      ```
      //将集合数据以指定值为起始值进行累计数值运算 => T reduce(T identity, BinaryOperator<T> accumulator);

      Arrays.asList(1,2,3).stream().reduce(0,(a,b) -> a + b)

      6
      ```
    * Collecting
      ```
      //将集合数据流转换为指定集合类型 => <R, A> R collect(Collector<? super T, A, R> collector);

      Arrays.asList(1, 2).stream().collect(Collectors.toSet());

      [1, 2]
      ```

> 内置函数式接口的分类与使用
  * 前言：在Java8之前，在需要使用匿名方法的场景时需要new该匿名类的实现，如线程池中使用匿名方法run()，需new Runnable类且实现run()方法；在Java8之后，可使用lambda表达式简化这一过程，直接使用函数式描述方法参数以及方法体，如下：
    ```
    ExecutorService executorService = Executors.newSingleThreadExecutor();

    //ExecutorService using class
    executorService.submit(new Runnable() {
        @Override
        public void run() {
            log.info("using class new runnable");
        }
    });
    
    //ExecutorService using lambda
    executorService.submit(()->log.info("using lambda new runnable"));
    ```
    只有匿名类含有类注解@FunctionalInterface时才可使用lambda表达式
    ```
    @FunctionalInterface
    public interface Runnable {
        public abstract void run();
    }
    ```
  * Functional Interface，是指带有@FunctionalInterface的Interface，它的特点是有且只有一个抽象方法，如果抽象方法前面携带default关键字则不做计算。Functional Interface一般都在java.util.function包中，根据需实现的方法参数和返回值，可分为多种Functional Interface。
  * 
   

> Lambda表达式实践

> Stream实践