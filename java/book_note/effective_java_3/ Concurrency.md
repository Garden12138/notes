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

> executor 、task 和 stream 优先于线程

> 并发工具优于 wait 和 notify

> 文档应包含线程安全属性

> 明智审慎的使用延迟初始化

> 不要依赖线程调度器