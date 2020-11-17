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
  * Function接口：定义了一个抽象方法apply，包含一个参数（T），一个返回（R）。
    ```
    @FunctionalInterface
    public interface Function<T, R> {
    /**
     * Applies this function to the given argument.
     *
     * @param t the function argument
     * @return the function result
     */
    R apply(T t);

    ...
    }
    ```
    常用于集合类处理，如存储一个以字符串为key，字符串长度为value的键值对，使用map.computeIfAbsent方法；computeIfAbsent方法使用Function接口的apply方法，参数为K类型，返回为V类型。
    ```
    Map<String, Integer> nameMap = new HashMap<>();
    Integer value = nameMap.computeIfAbsent("name", s -> s.length());

    4
    ```
    ```
    default V computeIfAbsent(K key,
            Function<? super K, ? extends V> mappingFunction) {
        Objects.requireNonNull(mappingFunction);
        V v;
        if ((v = get(key)) == null) {
            V newValue;
            if ((newValue = mappingFunction.apply(key)) != null) {
                put(key, newValue);
                return newValue;
            }
        }

        return v;
    }
    ```
    Function并没有指名具体参数类型以及返回类型，若需要传入特定类型参数，可使用IntFunction，LongFunction，DoubleFunction。
    ```
    @FunctionalInterface
    public interface IntFunction<R> {
    /**
     * Applies this function to the given argument.
     *
     * @param value the function argument
     * @return the function result
     */
    R apply(int value);
    }
    ```
    若需要返回特定类型值，可使用ToIntFunction，ToLongFunction，ToDoubleFunction。
    ```
    @FunctionalInterface
    public interface ToDoubleFunction<T> {
    /**
     * Applies this function to the given argument.
     *
     * @param value the function argument
     * @return the function result
     */
    double applyAsDouble(T value);
    }
    ```
    若需要同时传入特定类型参数和返回特定类型值，可使用DoubleToIntFunction, DoubleToLongFunction, IntToDoubleFunction, IntToLongFunction, LongToIntFunction, LongToDoubleFunction。
    ```
    @FunctionalInterface
    public interface LongToIntFunction {
    /**
     * Applies this function to the given argument.
     *
     * @param value the function argument
     * @return the function result
     */
    int applyAsInt(long value);
    }
    ```
  * BiFunction接口：定义了一个抽象方法apply，包含两个参数（T，U），一个返回（R）。
    ```
    @FunctionalInterface
    public interface BiFunction<T, U, R> {
    /**
     * Applies this function to the given arguments.
     *
     * @param t the first function argument
     * @param u the second function argument
     * @return the function result
     */
    R apply(T t, U u);
    ```
    常用于集合类处理，如计算指定Key的键值对的Value值，使用map.replaceAll方法；replaceAll方法使用BiFunction接口的apply方法，参数为K，V类型，返回为V类型。
    ```
    Map<String, Integer> salaries = new HashMap<>();
    salaries.put("alice", 100);
    salaries.put("jack", 200);
    salaries.put("mark", 300);
    salaries.replaceAll((name, oldValue) -> name.equals("alice") ? oldValue : oldValue + 200);
    ```
    ```
    default void replaceAll(BiFunction<? super K, ? super V, ? extends V> function) {
        Objects.requireNonNull(function);
        for (Map.Entry<K, V> entry : entrySet()) {
            K k;
            V v;
            try {
                k = entry.getKey();
                v = entry.getValue();
            } catch(IllegalStateException ise) {
                // this usually means the entry is no longer in the map.
                throw new ConcurrentModificationException(ise);
            }

            // ise thrown from function is not a cme.
            v = function.apply(k, v);

            try {
                entry.setValue(v);
            } catch(IllegalStateException ise) {
                // this usually means the entry is no longer in the map.
                throw new ConcurrentModificationException(ise);
            }
        }
    }
    ```
    若需要返回特定类型值，可使用ToIntBiFunction，ToLongBiFunction，ToDoubleBiFunction。
    ```
    @FunctionalInterface
    public interface ToIntBiFunction<T, U> {
    /**
     * Applies this function to the given arguments.
     *
     * @param t the first function argument
     * @param u the second function argument
     * @return the function result
     */
    int applyAsInt(T t, U u);
    }
    ```
  * Supplier接口：定义了一个抽象方法get，包含一个返回（T）,没有参数。
    ```
    @FunctionalInterface
    public interface Supplier<T> {
    /**
     * Gets a result.
     *
     * @return a result
     */
    T get();
    }
    ```
    常用于创建对象，如编写一个用户生成工厂。
    ```
    //用户生成工厂Bean
    @Bean
    public Supplier<User> userSupplier() {
      return () -> {
        User user = new User(UUID.randomUUID().toString());
        return user;
      };
    }
    //客户端调用
    @Autowired
    private Supplier<User> userSupplier;
    public void useUserSupplier() {
      //每次调用get()方法都会重新创建一个新对象
      User user1 = userSupplier.get();
      User user2 = userSupplier.get();
      System.out.println(user1 == user2);
    }

    fasle
    ```
    若需要返回特定类型值，可使用IntSupplier，LongSupplier，DoubleSupplier，BooleanSupplier。
    ```
    @FunctionalInterface
    public interface BooleanSupplier {
    /**
     * Gets a result.
     *
     * @return a result
     */
    boolean getAsBoolean();
    }
    ```
  * Consumer接口：定义了一个抽象方法accpet，包含一个参数（T），没有返回。
    ```
    @FunctionalInterface
    public interface Consumer<T> {
    /**
     * Performs this operation on the given argument.
     *
     * @param t the input argument
     */
    void accept(T t);
    ```
    常用于集合处理，如加工处理数组元素，使用list.forEach方法；forEach方法使用Consumer接口的accept方法，参数为T类型。
    ```
    List<Integer> list = new ArrayList<>();
    list.add(new Integer(1000));
    list.add(new Integer(2000));
    list.forEach(e -> e = e.intValue() + 1);

    1001
    2001
    ```
    ```
    default void forEach(Consumer<? super T> action) {
      Objects.requireNonNull(action);
      for (T t : this) {
        action.accept(t);
      }
    }
    ```
    若需要传入特定类型参数，可使用IntConsumer, LongConsumer, DoubleConsumer。
    ```
    @FunctionalInterface
    public interface DoubleConsumer {
    /**
     * Performs this operation on the given argument.
     *
     * @param value the input argument
     */
    void accept(double value);
    }
    ```
    若需要传入特定类型额外辅助参数，可使用ObjIntConsumer, ObjLongConsumer, ObjDoubleConsumer。
    ```
    @FunctionalInterface
    public interface ObjDoubleConsumer<T> {
    /**
     * Performs this operation on the given arguments.
     *
     * @param t the first input argument
     * @param value the second input argument
     */
    void accept(T t, double value);
    }
    ```
  * BiConsumer接口：定义了一个抽象方法accept，包含两个参数（T，U），没有返回。
    ```
    @FunctionalInterface
    public interface BiConsumer<T, U> {
    /**
     * Performs this operation on the given arguments.
     *
     * @param t the first input argument
     * @param u the second input argument
     */
    void accept(T t, U u);
    }
    ```
    常用于哈希映射的处理，如对哈希映射的键对应的值进行加工，使用map.forEach方法；forEach方法使用BiConsumer接口的accept方法，参数为K，V类型。
    ```
    map.forEach((key, value) -> value += 1);
    ```
    ```
    default void forEach(BiConsumer<? super K, ? super V> action) {
        Objects.requireNonNull(action);
        for (Map.Entry<K, V> entry : entrySet()) {
            K k;
            V v;
            try {
                k = entry.getKey();
                v = entry.getValue();
            } catch(IllegalStateException ise) {
                // this usually means the entry is no longer in the map.
                throw new ConcurrentModificationException(ise);
            }
            action.accept(k, v);
        }
    }
    ```
  * Predicate接口：定义了一个抽象方法test，包含一个参数（T），一个返回（boolean）。
    ```
    @FunctionalInterface
    public interface Predicate<T> {
    /**
     * Evaluates this predicate on the given argument.
     *
     * @param t the input argument
     * @return {@code true} if the input argument matches the predicate,
     * otherwise {@code false}
     */
    boolean test(T t);
    }
    ```
    常用于集合类过滤数据，如过滤集合List以'A'开头的元素，使用Stream的filter方法；filter方法使用Predicat接口的test方法，参数为P_OUT类型。
    ```
    List<String> elements = Arrays.asList("A", "B", "C", "D", "E");
    List<String> elementsWithA = elements.stream()
                                    .filter(e -> e.startsWith("A"))
                                    .collect(Collectors.toList());
    ```
    ```
    @Override
    public final Stream<P_OUT> filter(Predicate<? super P_OUT> predicate) {
        Objects.requireNonNull(predicate);
        return new StatelessOp<P_OUT, P_OUT>(this, StreamShape.REFERENCE,
                                     StreamOpFlag.NOT_SIZED) {
            @Override
            Sink<P_OUT> opWrapSink(int flags, Sink<P_OUT> sink) {
                return new Sink.ChainedReference<P_OUT, P_OUT>(sink) {
                    @Override
                    public void begin(long size) {
                        downstream.begin(-1);
                    }

                    @Override
                    public void accept(P_OUT u) {
                        if (predicate.test(u))
                            downstream.accept(u);
                    }
                };
            }
        };
    }
    ```
    若需要传入特定类型参数，可使用IntPredicate, LongPredicate, DoublePredicate。
    ```
    @FunctionalInterface
    public interface DoublePredicate {
    /**
     * Evaluates this predicate on the given argument.
     *
     * @param value the input argument
     * @return {@code true} if the input argument matches the predicate,
     * otherwise {@code false}
     */
    boolean test(double value);
    }
    ```
    若需要传入两个参数（T，U），可使用BiPredicate。
    ```
    @FunctionalInterface
    public interface BiPredicate<T, U> {
    /**
     * Evaluates this predicate on the given arguments.
     *
     * @param t the first input argument
     * @param u the second input argument
     * @return {@code true} if the input arguments match the predicate,
     * otherwise {@code false}
     */
    boolean test(T t, U u);
    }
    ```
  * Operator接口：根据操作目可分为UnaryOperator BinaryOperator两大类，其又可分为IntUnaryOperator，LongUnaryOperator，DoubleUnaryOperator，IntBinaryOperator，LongBinaryOperator，DoubleBinaryOperator，接收和返回相同的类型。
  ```
  @FunctionalInterface
  public interface IntUnaryOperator {
    /**
     * Applies this operator to the given operand.
     *
     * @param operand the operand
     * @return the operator result
     */
    int applyAsInt(int operand);
  }
  ```
  常用于集合数据多目运算，如计算整型集合list元素值之和，使用Stream的reduce方法；reduce方法使用BinaryOperator接口的apply方法，参数为U类型。
  ```
  List<Integer> values = Arrays.asList(1, 2, 3, 4, 5);
  int sum = values.stream().reduce(0, (i1, i2) -> i1 + i2);

  15
  ```
  ```
  @Override
  public final P_OUT reduce(final P_OUT identity, final BinaryOperator<P_OUT> accumulator) {
    return evaluate(ReduceOps.makeRef(identity, accumulator, accumulator));
  }

  public static <T, U> TerminalOp<T, U>
    makeRef(U seed, BiFunction<U, ? super T, U> reducer, BinaryOperator<U> combiner) {
        Objects.requireNonNull(reducer);
        Objects.requireNonNull(combiner);
        class ReducingSink extends Box<U> implements AccumulatingSink<T, U, ReducingSink> {
            @Override
            public void begin(long size) {
                state = seed;
            }

            @Override
            public void accept(T t) {
                state = reducer.apply(state, t);
            }

            @Override
            public void combine(ReducingSink other) {
                state = combiner.apply(state, other.state);
            }
        }
        return new ReduceOp<T, U, ReducingSink>(StreamShape.REFERENCE) {
            @Override
            public ReducingSink makeSink() {
                return new ReducingSink();
            }
        };
  }
  ```

> Lambda表达式实践
  * 优先使用标准Functional接口：java8在java.util.function包中定义的标准Functional接口，基本涵盖所需的各种类型，避免重复造轮子。比如：
    ```
    //重复造轮子
    //自定义Functional Interface
    @FunctionalInterface
    public interface Usage {
      String method(String string);
    }
    //使用自定义Functional Interface
    public String test(String string, Usage usage) {
      return usage.method(string);
    }
    //使用标准Functional Interface
    public String test(String string, Function<String, String> fn) {
      return fn.apply(string);
    }
    ```
  * 使用注解@FunctionalInterface：注解@FunctionalInterface非必须，但使用其可以避免在违背Functional Interface定义时报警。
  * 定义Functional Interfaces不滥用Default Methods：Functional Interface中只包含一个抽象未实现的方法，如果该Interface中还有其他抽象方法，可以使用default关键字为其提供一个默认实现，由于class是可多实现Interface，若滥用Default Methods，容易造成多个Interface之间定义相同的default方法，则会报错。
  * 使用Lambda表达式来实例化Functional Interface：
    ```
    //使用new关键字实例化
    Function<String,Integer> function = new Function<String, Integer>() {
            @Override
            public Integer apply(String s) {
                return Integer.parseInt(s);
            }
    };
    //使用Lambda表达式实例化
    Function<String,Integer> function = s -> Integer.parseInt(s);
    ```
  * 不重写以Functional Interface为参数的方法：
    ```
    public class ProcessorImpl implements Processor {
      @Override
      public String process(Callable<String> c) throws Exception {
        // implementation details
      }
      
      @Override
      public String process(Supplier<String> s) {
        // implementation details
      }
    }
    ```
    两个方法名是一样的，只有入参不同，但两个参数都为Functional Interface，都可以用相同的Lambda表达式表示，在使用时由于不知道调用哪个方法，故会报错。解决办法就是不重写，使用不同的方法名。
    ```
    String result = processor.process(() -> "test");
    ```
  * Lambda表达式不会定义新的作用域范围：使用Lambda表达式可以顶替内部类，但Lambda表达式和内部类是不同的，Lambda表达式并没有定义新的作用域范围，若在表达式中使用this是指向外部类，而内部类则会定义新的作用域范围，使用this则指向内部类本身。
  * Lambda表达式尽可能简洁：
    ```
    //Java通过类型推断来判断入参数类型。故Lambda表达式中可不传参数类型
    (a, b) -> a.toLowerCase() + b.toLowerCase(); => (String a, String b) -> a.toLowerCase() + b.toLowerCase();
    //若只有一个参数，可不需带口号
    a -> a.toLowerCase(); => (a) -> a.toLowerCase();
    //返回值可不需带return
    a -> a.toLowerCase(); => a -> return a.toLowerCase();
    //在可使用方法引用时使用方法引用
    String::toLowerCase; => a -> a.toLowerCase();
    ```
  * Lambda表达式内使用Effectively Final变量：这是近似final变量的意思，只要一个变量被赋值一次，那边编译器将会标志这个变量为Effectively Final变量，由于Lambda表达式经常使用在并行计算的场景中，故支持Effectively Final变量，不支持non-final变量，当有多个线程访问变量时就可防止不可预料的修改。
    ```
    String localVariable = "localVariable";
    Function<String,String> function = s -> {
      localVariable = s; //编译报错
      return s;
    };
    ```
  * Lambda表达式的异常处理：
    * 处理Unchecked Exception：
      ```
      //1.直接在lambda内捕获异常并处理
      list.forEach(i -> {
        try {
          System.out.println(1 / i);
        }catch (ArithmeticException ae) {
          System.err.println("ArithmeticException occured：" + ae.getMessage());
        }
      });
      //2.使用自定义异常封装类
      list.forEach(LambdaUncheckedExceptionWrapper.consumerWrapperWithExceptionClass(
        i -> System.out.println(1 / i),ArithmeticException.class));

      public class LambdaUncheckedExceptionWrapper {
        /**
        * Consumer函数式接口参数的非检查异常处理封装方法
        * @param consumer Consumer函数式接口参数
        * @param clazz 异常类
        * @param <T> Consumer函数式接口参数类型
        * @param <E> 异常类类型
        * @return
        */
        public static <T, E extends Exception> Consumer<T> consumerWrapperWithExceptionClass(Consumer<T> consumer, Class<E> clazz) {
          return i -> {
            try {
              consumer.accept(i);
            } catch (Exception ex) {
                try {
                    E exCast = clazz.cast(ex);
                    System.err.println(clazz.getName() + " occured : " + exCast.getMessage());
                } catch (ClassCastException ccEx) {
                    throw ex;
                }
              }
          };
        }
       }
      ```
    * 处理Checked Exception：
      ```
      static void throwIOException(Integer integer) throws IOException {
      }

      //直接在lambda内捕获异常或处理
      list.forEach(i -> {
        try {
          throwIOException(i);
        } catch (IOException e) {
          throw new RuntimeException(e);
        }
      });
      ```
> Stream实践
  * 实现if/else逻辑：可使用filter改写if/else实现逻辑。
    ```
    //传统写法
    list.stream().forEach(e -> {
      if(e.intValue % 2 == 0) {
        //输出偶数
        System.out.println(e + " is even number");
      }else{
        //输出奇数
        System.out.println(e + " is odd number");
      }
    });
    //filter写法
    list.stream().filter(e -> e.intValue % 2 == 0).forEach(e -> System.out.println(e + " is even number"));
    list.stream().filter(e -> e.intValue % 2 != 0).forEach(e -> System.out.println(e + " is odd number"));
    ```
  * Map使用Stream：
    * Map基本概念
      ```
      //创建一个Map
      Map<String,String> map = new HashMap<>();
      //获取Map的键值对集合
      Set<Map.Entry<String,String>> entrySet = map.entrySet();
      //获取Map的键集合
      Set<String> keySet = map.keySet();
      //获取Map的值集合
      Collection<String> values = map.values();
      ```
      Map本身没有Stream，但可通过上述转换成Set，Collection使用Stream。
      ```
      Stream<Map.Entry<String, String>> entrySetStream = entrySet.stream();
      Stream<String> keyStream = keySet.stream();
      Stream<String> valuesStream = values.stream();
      ```
    * 使用Stream获取Map符合某些条件value的key
      ```
      List<String> list = entrySetStream.filter(e -> "20".equals(e.getValue()))
                                        .map(Map.Entry::getKey)
                                        .collect(Collectors.toList);
      System.out.println(list);
      ```
    * 使用Stream获取Map符合某些条件key的value
      ```
      List<String> list = entrySetStream.filter(e -> "garden".equals(e.getKey())
                                        .map(Map.Entry::getValue)
                                        .collect(Collectors.toList);
      System.out.println(list);
      ```
  * Stream中使用peek：
    * peek的定义：
      ```
      Stream<T> peek(Consumer<? super T> action)
      ```
    * java8的Stream是由数据源，零个或一个或多个中间操作，零个或多个终止操作构成，peek属于中间操作，是lazy操作，需要等待终止操作才会执行，终止操作是Stream的启动操作，故peek需要结合终止操作使用才有效果。 
      ```
      //只使用peek操作，Stream不执行
      Stream<String> stream = Stream.of("one", "two", "three","four");
      stream.peek(System.out::println); //没有任何输出
      ```
    * 常用于中间操作的debug
      ```
      Stream.of("one", "two", "three","four").filter(e -> e.length() > 3)
                .peek(e -> System.out.println("Filtered value: " + e))
                .map(String::toUpperCase)
                .peek(e -> System.out.println("Mapped value: " + e))
                .collect(Collectors.toList());

      Filtered value: three
      Mapped value: THREE
      Filtered value: four
      Mapped value: FOUR
      ```