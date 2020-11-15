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

> Stream实践