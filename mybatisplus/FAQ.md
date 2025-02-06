## 常见问题

> 并发更新（更新值依赖于原始值）的问题

  * 问题写法：

     ```java
     LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
     queryWrapper.eq(User::getUsername, username);
     User user = this.getOne(queryWrapper);
     if (null == user) {
        throw new RuntimeException("用户不存在");
     }
     user.setAge(user.getAge() + 1);
     this.updateById(user);
     ```
     当多个并发请求时，可能同时读取同一用户的当前年龄，并基于这个值进行递增操作，这可能导致“丢失更新”。
  
  * 乐观锁解决方式：
    
    ```java
    LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
     queryWrapper.eq(User::getUsername, username);
     User user = this.getOne(queryWrapper);
     if (null == user) {
        throw new RuntimeException("用户不存在");
    }
    LambdaUpdateWrapper<User> updateWrapper = new LambdaUpdateWrapper<>();
    updateWrapper.eq(User::getId, user.getId())
                 .eq(User::getVersion, user.getVersion())
                 .set(User::getAge, user.getAge() + 1)
                 .set(User::setVersion, user.getVersion() + 1);
    boolean updatet = this.update(updateWrapper);
    // 乐观锁更新冲突失败（版本号已更新），抛出异常
    if (!updatet) {
        throw new RuntimeException("更新失败");
    }
    ```
    乐观锁在更新数据时，先查询出当前数据，然后对比当前版本号是否与数据库中的版本号相同，如果相同，则更新数据，否则，更新失败。

  * 悲观锁解决方式：
    
    ```java
    User user = selectByUsernameForUpdate(id); // 使用SELECT ... FOR UPDATE查询语句，获取排他锁
    if (null == user) {
        throw new RuntimeException("用户不存在");
    }
    user.setAge(user.getAge() + 1);
    this.updateById(user);
    ```
    悲观锁在更新数据时，会对数据加锁，其他并发请求只能等待锁释放后才能继续执行。

  * 数据库原子性解决方式：

    ```mysql
    UPDATE user SET age = age + 1 WHERE username = #{username}
    ```
    数据库原子性保证了多个并发请求对同一资源的更新操作的原子性，不会出现“丢失更新”的问题。

  * 适用场景选择：

    * 对于读多写少的场景，可以使用乐观锁，但需处理更新冲突失败的情况；
    * 对于频繁更新的场景，可以使用悲观锁，但会影响数据库性能，且确保数据库事务设置正确；
    * 最推荐的是使用数据库原子性方式，数据库系统内部会管理必要的锁，以确保每次更新都基于最新的数据，从而避免了并发更新导致的问题。

> 参考文献

* [Mybatis plus并发更新时的问题](https://blog.csdn.net/weixin_39973810/article/details/134535908)