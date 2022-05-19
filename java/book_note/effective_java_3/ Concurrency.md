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

> 文档应包含线程安全属性

> 明智审慎的使用延迟初始化

> 不要依赖线程调度器