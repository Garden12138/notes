## EffectiveJava3

#### 并发

> 同步访问共享的可变数据
  * 关键字```synchronized```可以保证在同一时刻，只有一个线程可以执行某一个方法或某一代码块。其产生的同步效果包含着互斥概念，即当一个对象被一个线程修改时，可以阻止另外一个线程观察到对象内部不一致的状态，对象被创建时处于一致的状态，当方法访问它时，则发生锁定，当这些方法观察到对象的状态时，可能会引起状态转变（对象从一种一致状态转换到另一种一致的状态）。同步不仅可以阻止一个线程看到对象处于不一致的状态中，它还可以保证进入同步方法或同步代码块的每个线程，都能看到由用一个锁保护的修改效果。
  * ```Java```语言规范保证读或写一个变量（```double```或```long```类型除外）是原子的，可以保证返回值是某个线程保存在该变量中的，即使多个线程在没有同步的情况下并发修改这个变量。为了提供性能，在读或写原子数据时，避免使用同步的做法是错误的，因为```Java```语言规范中的内存模型规定一个线程所做的变化时间以及变化内容对于其他线程是可以见的，为了在线程之间进行可靠的通信以及互斥访问，同步是必要的。如实现一个线程阻止另一个线程（不推荐使用```Java```类库的```Thread.stop```的不安全方法）：
    ```
    // 失败的方式
    public class StopThread { 
        private static Boolean stopRequested; 
        
        public static void main(String[] args) throws InterruptedException { 
            Thread backgroundThread = new Thread(() -> { 
                int i = 0; 
                while (!stopRequested) 
                    i++; 
            }); 
            
            backgroundThread.start(); 
            TimeUnit.SECONDS.sleep(1); 
            stopRequested = true; 
        } 
    }
    ```
    由于没有进行同步，不能保证后台线程获取主线程对```stopRequested```值的改变。使用```synchronized```同步声明读和取```stopRequested```变量值的方法：
    ```
    public class StopThread { 
        private static Boolean stopRequested; 
        
        private static synchronized void requestStop() { 
            stopRequested = true; 
        }
        
        private static synchronized Boolean stopRequested() { 
            return stopRequested; 
        }
        
        public static void main(String[] args) throws InterruptedException {
            Thread backgroundThread = new Thread(() -> { 
                int i = 0; 
                while (!stopRequested()) 
                    i++; 
            }); 
            
            backgroundThread.start(); 
            TimeUnit.SECONDS.sleep(1); 
            requestStop(); 
        } 
    }
    ```
    上述同步的方法只是为了线程之间的通信，不使用互斥访问，此时使用关键```volatile```（不执行互斥访问，可以保证任何一个线程在读取声明字段时取最新值）声明```stopRequested```变量，可提高性能：
    ```
    public class StopThread { 
        private static volatile Boolean stopRequested; 
        
        public static void main(String[] args) throws InterruptedException {
            Thread backgroundThread = new Thread(() -> { 
                int i = 0; 
                while (!stopRequested) 
                    i++; 
            }); 
            
            backgroundThread.start(); 
            TimeUnit.SECONDS.sleep(1); 
            stopRequested = true; 
        } 
    }
    ```
  * 谨慎使用```volatile```，如设计一个产生序列号的方法：
    ```
    private static volatile int nextSerialNumber = 0; 
    
    public static int generateSerialNumber() { 
        return nextSerialNumber++; 
    }
    ```
    这个方法无法保证每个调用都返回不同的值，因为增量操作符号```++```不具备原子性，它在```nextSerialNumber```字段中执行两个操作：首先读取值，然后写回一个新值，如果第二个线程在第一个线程读取旧值和写回新值之间读取这个字段，第二个线程就会与第一个线程观察到同一个值并且返回相同的序列号，造成安全性失败，导致程序计算出错误的结果。一种解决方法是声明中新增```synchronized```修饰符，确保多个调用不会交叉存取。还有一种方法是使用```AtomicLong```类，它```java.util.concurrent.atomic```的组成部分，这个包在单个变量上进行免锁定、线程安全的编程提供了基本类型：
    ```
    private static final Atomiclong nextSerialNum = new Atomiclong(); 
    
    public static long generateSerialNumber() { 
        return nextSerialNum.getAndIncrement(); 
    }
    ```
  * 一个线程在短时间内修改一个数据对象，然后其他线程没有进一步的同步也可以读取状态一致的对象，这种对象称为高效不变，将这种对象引用从一个线程传递到其他的线程被称为安全发布。安全发布对象引用方式有多种：
    * 将对象保存在静态字段中，作为类初始化的一部分。
    * 将对象保存在```volatile```字段、```final```字段或者通过正常锁定访问的字段中。
    * 将对象放到并发集合中。

> 避免过度同步
  * 为了避免活性失败和安全性失败，在一个被同步的区域内部（方法或代码块），不设计成可被覆盖的方法或由客户端以函数对象形式提供的方法。外来方法的作用，从同步区域中调用它会导致异常、死锁或者数据损坏。设计一个可以观察到的集合包装类，该类允许客户端将元素添加至集合中时预定通知：
    ```
    public class ObservableSet<E> extends ForwardingSet<E> { 
        public ObservableSet(Set<E> set) { 
            super(set); 
        } 
        
        private final List<SetObserver<E>> observers = new ArrayList<>();
         
        public void addObserver(SetObserver<E> observer) { 
            synchronized(observers) { 
                observers.add(observer); 
            } 
        }
        
        public Boolean removeObserver(SetObserver<E> observer) { 
            synchronized(observers) { 
                return observers.remove(observer); 
            } 
        }
        
        private void notifyElementAdded(E element) { 
            synchronized(observers) {
                for (SetObserver<E> observer : observers) 
                    observer.added(this, element); 
            } 
        }
        
        @Override 
        public Boolean add(E element) { 
            Boolean added = super.add(element); 
            if (added) 
                notifyElementAdded(element); 
            return added; 
        }
        
        @Override
        public Boolean remove(E element) {
            return super.remove(element);
        }
    } 
    ```
    ```
    @FunctionalInterface 
    public interface SetObserver<E> { 
        void added(ObservableSet<E> set, E element); 
    }
    ```
    简单的客户端调用，```ObservableSet```是正常的，如打印0～99的数字：
    ```
    public static void main(String[] args) {
        ObservableSet<Integer> set = new ObservableSet<>(new HashSet<>());
        set.addObserver((s, e) -> System.out.println(e));
        for(int i = 0; i <100; i++) {
            set.add(i);
        }
    }
    ```
    若传入的观察者的支持当添加到集合的值为23，将该观察者删除：
    ```
    public static void main(String[] args) {
        ObservableSet<Integer> set = new ObservableSet<>(new HashSet<>());
        set.addObserver(new SetObserver<>() { 
            public void added(ObservableSet<Integer> s, Integer e) { 
                System.out.println(e); 
                if (e == 23) 
                    s.removeObserver(this); 
            } 
        });
        for(int i = 0; i <100; i++) {
            set.add(i);
        }
    }
    ```
    该程序会打印数字0～23，然后抛出```ConcurrentModificationException```异常。由于```notifyElementAdded```调用观察者的```added```方法时正处于遍历观察者列表阶段，此时```added```方法调用移除观察者列表元素的方法```removeObserver```，造成遍历元素列表的同时删除列表元素的异常错误。

    若使用另外一个线程试图取消观察者：
    ```
    public static void main(String[] args) {
        ObservableSet<Integer> set = new ObservableSet<>(new HashSet<>());
        set.addObserver(new SetObserver<>() { 
            public void added(ObservableSet<Integer> s, Integer e) { 
                System.out.println(e); 
                if (e == 23) { 
                    ExecutorService exec = Executors.newSingleThreadExecutor(); 
                    try {
                        exec.submit(() -> s.removeObserver(this)).get(); 
                    } catch (ExecutionException | InterruptedException ex) {
                        throw new AssertionError (ex); 
                    }
                    finally { 
                        exec.shutdown(); 
                    } 
                } 
            } 
        });
        for(int i = 0; i <100; i++) {
            set.add(i);
        }
    }
    ```
    运行该程序时，没有遇到异常而出现死锁。主线程拥有锁，而后台线程等待释放锁，此时主线程等待后台线程完成对观察者的删除从而释放锁，故造成死锁。

    解决上述出现的异常和死锁问题，关键将外来方法的调用移出同步的区域，同步区域生成观察者列表的快照，如：
    ```
    private void notifyElementAdded(E element) { 
        List<SetObserver<E>> snapshot = null; 
        synchronized(observers) { 
            snapshot = new ArrayList<>(observers); 
        }
        for (SetObserver<E> observer : snapshot) 
            observer.added(this, element); 
    }
    ```
    还可以使用```Java```类库提供的并发集合```CopyOnWriteArrayList```，通过重新拷贝整个底层数组，实现所有的写操作，由于内部数组永远不改动，因此迭代不需要锁定：
    ```
    private final List<SetObserver<E>> observers = new CopyOnWriteArrayList<>(); 
    
    public void addObserver(SetObserver<E> observer) {
        observers.add(observer); 
    }
    
    public Boolean removeObserver(SetObserver<E> observer) { 
        return observers.remove(observer); 
    }
    
    private void notifyElementAdded(E element) {
        for (SetObserver<E> observer : observers)
            observer.added(this, element); 
    }
    ```
  * 通常在同步区域内做尽可能少的工作，一般为获得锁，检查共享数据，根据需要转换数据，然后释放锁。若执行某个耗时的操作，则应该设法将耗时操作移出同步区域。
  * 不过度同步，在多核的场景下，过度同步会因为等待获取锁失去并行的机会且会限制虚拟机优化代码执行的能力。

> executor 、task 和 stream 优先于线程
  * 工作队列（```work queue```）实现方式不正确容易出现安全问题或导致活性失败。```Java```平台后续新增的```java.util.concurrent```包，它可以简化任务的执行，其包含一个```Executor Framework```是基于接口的任务执行工具。创建工作队列：
    ```
    ExecutorService exec = Executors.newSingleThreadExecutor();
    ```
    提交一个```runnable```方法：
    ```
    exec.execute(runnable);
    ```
    优雅终止：
    ```
    exec.shutdown();
    ```
  * ```executor service```可以完成更多的工作：
    * 可以等待一个任务集合中的任何任务或所有任务完成（利用```invokeAny```或```invokeAll```）。
    * 可以等待```executor service```优雅地完成终止（利用```awaitTermination```）。
    * 可以在任务完成时逐个获取这些任务的结果（利用```ExecutorCompletionService```）。
    * 可以调度在某个特殊的时间段定时运行或者阶段性地运行任务（利用```ScheduledThreadPoolExcutor```）。
  * 选择合适的```executor service```：
    * 如果编写小程序或轻量负载的服务器，使用```Executors.newCachedThreadPool```。
    * 大负载的产品服务器，使用```Executors.newFixedThreadPool```。
    * 如果需要包含固定线程数目的线程池或最大限度控制线程，使用```ThreadPoolExecutor```类。
  * ```Executor```优于直接使用线程。在```Executor Framewokr```中工作单元和执行机制时分开的，工作单元称为任务，分别有```Runnable```以及```Callable```，执行任务的通用机制是```Executor Service```。从任务的角度选择一个合适的```executor service```执行任务从而解决实际问题。```Java7```中```Executor```框架扩展为支持```fork-join```任务，这些任务在```fork-join```池服务运行，该任务用```ForkJoinTask```实例表示，可以被分为更小的子任务，```ForkJoinPool```的线程不仅要处理这些任务，还会从另外线程争取执行任务，以确保所有的线程保持忙碌，从而提高```CPU```使用率、提高吞吐量并降低延迟。```Java8```的并行流在```ForkJoinPool```基础上实现的，必要时使用```Stream```优于直接使用线程。

> 并发工具优于 wait 和 notify
  * ```Java5```发行版本开始，更高级的并发工具逐渐代替手工编写```wait```和```notify```来完成各项并发工作。并发工具包```java.util.concurrent```中的高级工具分为三类：```Executor Framework```、并发集合（```Concurrent Collection```）以及同步器（```Synchronizer```）。
  * 并发集合为标准集合（```List```、```Queue```和```Map```）提供了高性能的并发实现。为了提高并发性，这些实现在内部实现自我管理同步，故并发集合不可能排除并发活动，将它锁定会使程序速度变慢。一些并发集合已经通过依赖状态的修改操作进行了拓展，它将几个基本操作合并到单个原子操作中，它们通过缺省方法加入```Java8```对应的集合接口中。如使用```Map```的```putIfAbsent(key, value)```方法实现线程安全的```Map```。设计一个模拟```String.intern```的方法：
    ```
    private static final ConcurrentMap<String, String> map = new ConcurrentHashMap<>(); 
    
    public static String intern(String s) { 
        String previousValue = map.putIfAbsent(s, s); 
        return previousValue == null ? s : previousValue; 
    }
    ```
    使用```ConcurrentMap```的获取操作```get```方法可以进行优化：
    ```
    public static String intern(String s) { 
        String result = map.get(s); 
        if (result == null) { 
            result = map.putIfAbsent(s, s); 
            if (result == null) 
                result = s; 
        }
        return result; 
    }
    ```
    并发集合优于同步集合，如应该优先使用```ConcurrentMap```而不是```Collections.synchronizedMap```。
  * 同步器是使线程能够等待另一个线程的对象，允许它们协调动作，同步器有```CountDownLatch```、```Semaphore```、```CyclicBarrier```、```Exchanger```和```Phaser```。最常使用的倒计数锁存器（```CountDownLatch```）允许一个或多个线程等待一个或多个其他线程来完成某些任务，该同步器唯一的构造器带有一个```int```类型的参数，该参数指允许所有在等待的线程被处理之前，必须在锁存器上调用```coutDown```方法的次数。如设计一个待所有任务线程就绪后开始计时的计时方法：
    ```
    // Simple framework for timing concurrent execution 
    public static long time(Executor executor, int concurrency, Runnable action) throws InterruptedException { 
        CountDownLatch ready = new CountDownLatch(concurrency); CountDownLatch start = new CountDownLatch(1); 
        CountDownLatch done = new CountDownLatch(concurrency);
        
        for (int i = 0; i < concurrency; i++) { 
            executor.execute(() -> { 
                ready.countDown(); 
                // Tell timer we're ready 
                try {
                    start.await(); 
                    // Wait till peers are ready 
                    action.run();
                } catch (InterruptedException e) { 
                    Thread.currentThread().interrupt(); 
                } finally {
                    done.countDown(); 
                    // Tell timer we're done 
                } 
            }); 
        }
        
        ready.await(); 
        // Wait for all workers to be ready 
        long startNanos = System.nanoTime(); 
        start.countDown(); 
        // And they're off!
        done.await(); 
        // Wait for all workers to finish 
        return System.nanoTime() - startNanos; 
    }
    ```
  * 虽然优先使用并发工具，但可能会维护使用```wait```方法和```notify```方法的遗留方法。```wait```方法被用来使用线程等待某个条件，它必须在同步区域内部被调用，这个同步区域将对象锁定在调用```wait```方法的对象上，使用```wait```方法的标准模式：
    ```
    // The standard idiom for using the wait method 
    synchronized (obj) { 
        while (<condition does not hold>) 
            obj.wait(); 
            // (Releases lock, and reacquires on wakeup) 
            ... // Perform action appropriate to condition 
    }
    ```
    必须从```while```循环内部调用```wait```方法，在等待之前测试条件，当条件已经成立时就跳过等待，这对于确保活性时必要的；在等待之前测试条件，如果条件不成立时继续等待，这对于确保安全性是必要的。
    
    对于唤醒等待线程的方式```notify```和```notifyAll```，应该始终优先使用```notifyAll```方法，因为它可以确保将所有需要被唤醒的线程唤醒，虽然可能会唤醒其他无相关的线程，但这不影响程序的正确性，因为它们会检查正在等待的条件，如果条件不满足则会继续等待；从优化角度，如果处于等待状态的所有线程都在等待同一个条件且每次只有一个线程可以从这个条件中被唤醒，则优先使用```notify```方法。

> 文档应包含线程安全属性
  * 类在其方法并发使用时的行为是其与客户端约定的重要组成部分，若没有记录类在这一方面的行为，则用户可能会做出生成的程序可能缺少同步或过度同步的错误假设：
    * 通过在方法的文档中查找```synchronized```修饰符来判断方法是否线程安全是错误的。方法声明中```synchronized```修饰符的存在是实现细节而不是```API```的一部分，它不能表明方法是线程安全的。
    * 认为```synchronized```修饰符的存在足以记录线程安全性是错误的，因为线程安全分为几个级别，若需要启用安全的并发使用，类必须清楚地记录它支持的线程安全级别：
      * 不可变。类的实例看起来是常量，不需要外部同步。如```String```、```Long```和```BigInteger```。
      * 无条件线程安全。类的实例是可变的，类具有足够的内部同步，无需任何外部同步即可并发地使用该类的实例。如```AtomicLong```和```ConcurrentHashMap```。
      * 有条件线程安全。与无条件线程安全类似，只是有些方法需要外部同步才能安全并发使用。如```Collections.synchronized```包装器返回的集合，其迭代器需要外部同步。
      * 非线程安全。类的实例是可变的，并发使用它们客户端需要使用外部同步包围每个方法调用（或调用序列）。如```ArrayList```和```HashMap```。
      * 线程对立。即使每个方法调用都被外部同步包围，该类对于并发使用也是不安全的。线程对立通常是由于在不同步的情况下修改静态数据导致的。当发现类或方法不相容时则通常将其修复或弃用。
  * 线程安全级别（除线程对立外）使用的线程安全注解分为```Immutable```、```ThreadSafe```以及```NotThreadSafe```。无条件线程安全和有条件线程安全都包含在```ThreadSafe```注解中。在文档记录有条件的线程安全类需要注意指出哪些调用序列需要外部同步以及执行这些序列必须获的锁对象，通常实例本身是锁，但也有例外如：
    ```
    It is imperative that the user manually synchronize on the returned map when iterating over any of its collection views:
    ```
    当用于遍历其集合视图时，必须手动同步返回的```Map```：
    ```
    Map<K, V> m = Collections.synchronizedMap(new HashMap<>()); 
    Set<K> s = m.keySet(); // Needn't be in synchronized block 
    ... 
    synchronized(m) { // Synchronizing on m, not s!
        for (K key : s) 
            key.f(); 
    }
    ```
  * 类的线程安全的描述通常属于该类的文档注释，但是具有特殊线程安全属性的方法应该在它们的文档注释中描述这些属性。没有必要记录枚举类型的不变性。静态工厂必须记录返回对象的线程安全性，除非可以从返回类型看出，如```Collections.synchronizedMap```。
  * 若编写一个无条件线程安全的类，请考虑使用一个私有锁对象来代替同步方法，这将保护免受客户端或者子类的同步干扰，并为提供更大的灵活性，以便在后续的版本中才有复杂的并发控制方式。

> 明智审慎的使用延迟初始化
  * 延迟初始化是延迟字段初始化，直到需要时才初始化字段，否则不初始化字段。该技术适用于实例字段或静态字段。延迟初始化的其中一个用途是优化，如果一个字段只在类的小部分实例上访问，并且初始化该字段的代价高，这时可以使用延迟初始化进行优化，还有一种用途可以用于破坏类中的有害循环和实例初始化。
  * 延迟初始化的最佳建议是除非需要，否则非必要使用这种技术，虽然它降低了初始化类或创建实例的成本，代价是增加访问延迟初始化字段的成本，初始化的开销以及初始化后访问每个字段的频率实际上损害性能。存在多线程的情况下，使用延迟初始化必须使用某种形式的同步，否则会导致严重的错误。
  * 延迟初始化的使用：
    * 在大多数情况下，常规初始化优于延迟初始化。
    * 使用同步访问器延迟初始化实例/静态字段；
      ```
      // 实例字段
      private FieldType field; 
      
      private synchronized FieldType getField() { 
          if (field == null)
              field = computeFieldValue(); 
          return field; 
      }
      ```
      ```
      // 静态字段
      private static FieldType field; 
      
      private static synchronized FieldType getField() { 
          if (field == null)
              field = computeFieldValue(); 
          return field; 
      }
      ```
    * 如果需要在静态字段上使用延迟初始化提高性能，使用```lazy initialization holder class```模式：
      ```
      private static class FieldHolder { 
          static final FieldType field = computeFieldValue(); 
      }
      
      private static FieldType getField() { 
          return FieldHolder.field; 
      }
      ```
      第一次调用```getField```时，它执行```FieldHolder.field```，导致初始化```FieldHolder```类。这个用法只执行字段访问，故延迟初始化实际上不会增加访问成本。```VM```只会对同步字段访问来初始化类并且在初始化类之后，```VM```会进行代码修补，对字段的后续访问不会设计任何测试或同步。
    * 如果需要在实例字段上使用延迟初始化提高性能，使用双重检查模式：
      ```
      private volatile FieldType field;
      
      private FieldType getField() { 
          FieldType result = field; 
          if (result == null) { // First check (no locking)
              synchronized(this) { 
                  if (field == null) // Second check (with locking)
                      field = result = computeFieldValue(); 
              } 
          }
          return result; 
      }
      ```
      若实例字段允许重复初始化，则使用单检查模式：
      ```
      private volatile FieldType field;
      
      private FieldType getField() { 
          FieldType result = field; 
            if (field == null)
                field = result = computeFieldValue(); 
            } 
          return result; 
      }
      ```
      若不关心每个线程是否重新计算字段的值，并且字段的类型是```long```或```double```之外的基本类型，可以使用原生单检查模式：
      ```
      private FieldType field;
      
      private FieldType getField() { 
          FieldType result = field; 
            if (field == null)
                field = result = computeFieldValue(); 
            } 
          return result; 
      }
      ```
      上述各模式都适用于基本类型和对象引用字段。当字段为数值基本类型字段，检查字段应该是0而不是```null```。

> 不要依赖线程调度器