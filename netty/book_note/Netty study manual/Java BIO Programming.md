## Java BIO 编程

### Java BIO 基本介绍

* ```Java BIO``` 是传统的 ```Java I/O``` 编程，其相关的类和接口在 ```java.io``` 包中。

* ```BIO(BlockingI/O)```：同步阻塞，服务器实现模式为一个连接一个线程，即客户端有连接请求时服务器端就需要启动一个线程进行处理。

* ```BIO``` 方式适用于连接数目比较小且固定的架构，这种方式对服务器资源要求比较高且低并发。

### Java BIO 工作机制

* 服务器端启动一个 ```ServerSocket``` 监听端口，等待客户端的连接。
* 客户端启动 ```Socket```对服务器进行通信，服务器端对每个客户端 ```Socket``` 请求都建立一个线程与之通讯。
* 客户端发出请求后，先咨询服务器是否有线程响应，若没有则会等待，或者被拒绝；若有响应，客户端线程会等待请求结束后，在继续执行。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/netty/netty2.png)

### Java BIO 应用实现

* 按照 ```BIO``` 方式编写一个简单的应用实现：

  ```java
  import java.io.InputStream;
  import java.net.ServerSocket;
  import java.net.Socket;
  import java.util.concurrent.ExecutorService;
  import java.util.concurrent.Executors;

  public class BIOServer {

      public static void main(String[] args) throws Exception {
          // 1. create a socket server that listens on port 8081
          ServerSocket serverSocket = new ServerSocket(8081);
          System.out.println("Socket server started on port 8081");
          // 2. create a thread pool to handle client requests
          ExecutorService newCachedThreadPool = Executors.newCachedThreadPool();
          while (true) {
              System.out.print("thread info id = " + Thread.currentThread().getId() + " name = " + Thread.currentThread().getName());
              System.out.println("waiting for client connection...");
              final Socket socket = serverSocket.accept(); // closed or not bound will throw an exception
              System.out.println("connected to a client");
              // 3. create a new thread to handle the client request
              newCachedThreadPool.execute(new Runnable() {
                  public void run() {
                      handler(socket);
                  }
              });
          }
      }

      public static void handler(Socket socket) {
          try {
              System.out.println("thread info id = " + Thread.currentThread().getId() + " name = " + Thread.currentThread().getName());
              byte[] bytes = new byte[1024];
              InputStream inputStream = socket.getInputStream();
              // 4. read the data from the client
              while (true) {
                  System.out.println("reading...");
                  int read = inputStream.read(bytes);
                  if (read != -1) {
                      System.out.println("received data: " + new String(bytes, 0, read));
                  } else {
                      break;
                  }
              }
          } catch (Exception e) {
              e.printStackTrace();
          } finally {
              // 5. close the connection to the client
              System.out.println("closing connection to client");
              try {
                  socket.close();
              } catch (Exception e) {
                  e.printStackTrace();
              }
          }
      }
  }
  ```

  效果：

  客户端1、2使用 ```telnet``` 命令（```telnet localhost 8081```）连接，服务端日志如下：

  ```bash
  Socket server started on port 8081
  thread info id = 1 name = mainwaiting for client connection...
  connected to a client
  thread info id = 1 name = mainwaiting for client connection...
  thread info id = 13 name = pool-1-thread-1
  reading...
  connected to a client
  thread info id = 1 name = mainwaiting for client connection...
  thread info id = 14 name = pool-1-thread-2
  reading...
  ```

  可以看出```BIO```模型的两个特点：

    * 阻塞，```serverSocket.accept()``` 会阻塞主线程，主线程一直等待客户端连接，没有客户端连接时，线程会一直等待； ```inputStream.read(bytes)``` 会阻塞工作线程，没有数据可读时，线程会一直等待。

    * 同步，指 ```I/O``` 操作是顺序执行的，如必须等待 ```read()``` 结果返回后，才能继续执行后续代码。

### Java BIO 问题分析

* 服务器端创建过多线程，占用系统资源过多，容易造成服务器资源不足。
* 当没有客户端连接或没有数据可读时，主线程或工作线程一直阻塞，造成线程资源浪费。