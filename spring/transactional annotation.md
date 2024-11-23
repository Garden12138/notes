## @Transactional注解

> 简介

* 系统应用开发过程中经常需要使用事务来保证业务数据的一致性，如开启事务、执行数据库写操作、提交或回滚事务，这种标准实现方式适用于少量的一致性业务，如果存在大量的一致性业务，使用这种方式会让开发人员重复编码，造成代码冗余。```Spring```框架提供了```@Transactional```注解来简化这一过程，它管理事务的生命周期，并提供事务传播机制、事务隔离级别等功能。

> 使用@Transactional注解事务不生效的场景

* 事务注解没有指定检查异常：

  ```java
  /**
   * 保存以及抛出不正确的检查异常，事务不回滚
   *
   * @param user
   * @* @throws IOException
   */
  @Transactional(rollbackFor = {})
  public void saveAndThrowIncorrectCheckedException(User user) throws IOException {
      userMapper.insert(user);
      throw new IOException("saveAndThrowIncorrectCheckedException IOException...");
  }
  ```
* 内部调用事务注解方法：

  ```java
  /**
   * 内部保存
   *
   * @param user
   * @throws IOException
   */
  public void innerSave(User user) throws IOException {
    saveAndThrowCorrectCheckedException(user);
  }

  /**
   * 保存以及抛出正确的检查异常，事务回滚
   *
   * @param user
   * @throws IOException
   */
  @Transactional(rollbackFor = IOException.class)
  public void saveAndThrowCorrectCheckedException(User user) throws IOException {
      userMapper.insert(user);
      throw new IOException("saveAndThrowCorrectCheckedException IOException...");
  }
  ```

> 事务传播机制

* 事务传播机制是指当一个事务方法被另一个事务方法调用时，该事务方法应该如何进行事务处理。Spring支持以下几种事务传播机制：

  * REQUIRED（默认值）：如果当前存在事务，则使用该事务；如果当前没有事务，则创建一个新的事务：
    
    ```java
    @Transactional(propagation = Propagation.REQUIRED, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByRequiredPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByRequiredPropagation happened...");
    }

    /**
     * required传播机制-事务不存在则创建新的事务-插入回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/required/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/required/noExistTransaction")
    public String requiredNoExistTransaction(@RequestBody User user) {
        user.setId(1000L);
        propagationService.saveAndThrowRuntimeExceptionByRequiredPropagation(user);
        return "success";
    }

    /**
     * required传播机制-事务存在则使用已存在事务-两次插入都回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/required/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/required/existTransaction")
    @Transactional
    public String requiredExistTransaction(@RequestBody User user) {
        user.setId(1001L);
        userMapper.insert(user);
        try {
            user.setId(1002L);
            propagationService.saveAndThrowRuntimeExceptionByRequiredPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        return "success";
    }
    ```

  * REQUIRES_NEW：如果当前存在事务，则把当前事务挂起，创建一个新的事务，新的事务执行完成后，恢复原有事务的运行；如果当前没有事务，则创建一个新的事务：

    ```java
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByRequiredNewPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByRequiredNewPropagation happened...");
    }

    /**
     * requiredNew传播机制-事务不存在则创建新的事务-插入回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/requiredNew/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/requiredNew/noExistTransaction")
    public String requiredNewNoExistTransaction(@RequestBody User user) {
        user.setId(1003L);
        propagationService.saveAndThrowRuntimeExceptionByRequiredNewPropagation(user);
        return "success";
    }

    /**
     * requiredNew传播机制-事务存在则先挂起，然后创建新的事务-前者不回滚，后者回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/requiredNew/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/requiredNew/existTransaction")
    @Transactional
    public String requiredNewExistTransaction(@RequestBody User user) {
        user.setId(1004L);
        userMapper.insert(user);
        try {
            user.setId(1005L);
            propagationService.saveAndThrowRuntimeExceptionByRequiredNewPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        return "success";
    }
    ```

  * SUPPORTS：如果当前存在事务，则使用该事务；如果当前没有事务，则不使用事务进行业务处理：

    ```java
    @Transactional(propagation = Propagation.SUPPORTS, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionBySupportsPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionBySupportsPropagation happened...");
    }

    /**
     * supports传播机制-事务不存在则不使用事务-插入不回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/supports/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/supports/noExistTransaction")
    public String supportsNoExistTransaction(@RequestBody User user) {
        user.setId(1006L);
        propagationService.saveAndThrowRuntimeExceptionBySupportsPropagation(user);
        return "success";
    }

    /**
     * supports传播机制-事务存在则使用已存在事务-两次插入都回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/supports/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/supports/existTransaction")
    @Transactional
    public String supportsExistTransaction(@RequestBody User user) {
        user.setId(1007L);
        userMapper.insert(user);
        try {
            user.setId(1008L);
            propagationService.saveAndThrowRuntimeExceptionBySupportsPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        return "success";
    }
    ```

  * NOT_SUPPORTED：如果当前存在事务，则把当前事务挂起， 不使用事务进行业务处理，执行完成后，恢复原有事务的运行；如果当前没有事务，则不使用事务进行业务处理：

    ```java
    @Transactional(propagation = Propagation.NOT_SUPPORTED, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByNotSupportedPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByNotSupportedPropagation happened...");
    }

    /**
     * notSupported传播机制-事务不存在则不使用事务-插入不回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/notSupported/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/notSupported/noExistTransaction")
    public String notSupportedNoExistTransaction(@RequestBody User user) {
        user.setId(1009L);
        propagationService.saveAndThrowRuntimeExceptionByNotSupportedPropagation(user);
        return "success";
    }

    /**
     * notSupported传播机制-事务存在则先挂起事务，不使用事务运行，最后恢复事务-前者插入回滚，后者插入不回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/notSupported/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/notSupported/existTransaction")
    @Transactional
    public String notSupportedExistTransaction(@RequestBody User user) {
        user.setId(1010L);
        userMapper.insert(user);
        try {
            user.setId(1011L);
            propagationService.saveAndThrowRuntimeExceptionByNotSupportedPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        throw new RuntimeException("notSupportedExistTransaction happened...");
    }
    ```

  * MANDATORY：如果当前存在事务，则使用该事务；如果当前没有事务，则抛出异常：

    ```java
    @Transactional(propagation = Propagation.MANDATORY, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByMandatoryPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByMandatoryPropagation happened...");
    }

    /**
     * mandatory传播机制-事务不存在，抛出异常
     *
     * curl -X POST http://localhost:8081/springboot/propagation/mandatory/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/mandatory/noExistTransaction")
    public String mandatoryNoExistTransaction(@RequestBody User user) {
        user.setId(1012L);
        propagationService.saveAndThrowRuntimeExceptionByMandatoryPropagation(user);
        return "success";
    }

    /**
     * mandatory传播机制-事务存在则使用已存在事务-两次插入都回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/mandatory/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/mandatory/existTransaction")
    @Transactional
    public String mandatoryExistTransaction(@RequestBody User user) {
        user.setId(1013L);
        userMapper.insert(user);
        try {
            user.setId(1014L);
            propagationService.saveAndThrowRuntimeExceptionByMandatoryPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        return "success";
    }
    ```

  * NEVER：如果当前存在事务，则抛出异常；如果当前没有事务，则不使用事务进行业务处理：

    ```java
    @Transactional(propagation = Propagation.NEVER, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByNeverPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByNeverPropagation happened...");
    }

    /**
     * never传播机制-事务不存在则不使用事务-插入不回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/never/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/never/noExistTransaction")
    public String neverNoExistTransaction(@RequestBody User user) {
        user.setId(1015L);
        propagationService.saveAndThrowRuntimeExceptionByNeverPropagation(user);
        return "success";
    }

    /**
     * never传播机制-事务存在则抛出异常-前者插入回滚，后者抛出异常
     *
     * curl -X POST http://localhost:8081/springboot/propagation/never/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/never/existTransaction")
    @Transactional
    public String neverExistTransaction(@RequestBody User user) {
        user.setId(1016L);
        userMapper.insert(user);
        user.setId(1017L);
        propagationService.saveByNeverPropagation(user);
        return "success";
    }
    ```

  * NESTED：如果当前存在事务，则使用该事务；如果当前没有事务，则嵌套一个新的事务：

    ```java
    @Transactional(propagation = Propagation.NESTED, rollbackFor = RuntimeException.class)
    public void saveByNeverPropagation(User user) {
        userMapper.insert(user);
    }

    @Transactional(propagation = Propagation.NESTED, rollbackFor = RuntimeException.class)
    public void saveAndThrowRuntimeExceptionByNestedPropagation(User user) {
        userMapper.insert(user);
        throw new RuntimeException("saveAndThrowRuntimeExceptionByNestedPropagation happened...");
    }

    /**
     * nested传播机制-事务不存在则创建新的事务-插入回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/nested/noExistTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/nested/noExistTransaction")
    public String nestedNoExistTransaction(@RequestBody User user) {
        user.setId(1018L);
        propagationService.saveAndThrowRuntimeExceptionByNestedPropagation(user);
        return "success";
    }

    /**
     * nested传播机制-事务存在则先挂起，然后嵌套新的事务-前者不回滚，后者回滚
     *
     * curl -X POST http://localhost:8081/springboot/propagation/nested/existTransaction -H 'Content-Type: application/json' -d '{"userName": "Daemon", "age": 10}'
     *
     * @param user
     * @return
     * @throws IOException
     */
    @PostMapping("/nested/existTransaction")
    @Transactional
    public String nestedExistTransaction(@RequestBody User user) {
        user.setId(1019L);
        userMapper.insert(user);
        try {
            user.setId(1020L);
            propagationService.saveAndThrowRuntimeExceptionByNestedPropagation(user);
        } catch (Exception e) {
            System.out.println("捕获异常，防止内部异常影响观察结果！");
        }
        return "success";
    }
    ```

> 事务隔离级别

  * 读未提交（READ_UNCOMMITTED）：一个事务可以看到其他事务未提交的数据，可能会导致脏读、不可重复读、幻读：

    ```java
    @Transactional(isolation = Isolation.READ_UNCOMMITTED)
    public User readUnCommit(Long id) {
        return userMapper.selectById(id);
    }

    /**
     * 读未提交事务级别-读取到未提交的数据
     *
     * curl -X GET http://localhost:8081/springboot/isolation/readUnCommit?id=1019
     * @param id
     * @return
     */
    @GetMapping("/readUnCommit")
    public User readUnCommit(@RequestParam("id") Long id) {
        return isolationService.readUnCommit(id);
    }
    ```

  * 读已提交（READ_COMMITTED）：一个事务只能看到其他事务提交的数据，可以避免脏读，但是可能导致不可重复读、幻读：

    ```java
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public User readCommit(Long id) {
        User user = userMapper.selectById(id);
        log.info("{} before another transaction update", user.toString());
        try {
            log.info("another transaction doing update...");
            Thread.sleep(30 * 1000);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        user = userMapper.selectById(id);
        log.info("{} after another transaction update", user.toString());
        return user;
    }

    /**
     * 读已提交事务级别-前后多（两）次读取的数据不一样
     *
     * curl -X GET http://localhost:8081/springboot/isolation/readCommit?id=1019
     * @param id
     * @return
     */
    @GetMapping("/readCommit")
    public User readCommit(@RequestParam("id") Long id) {
        return isolationService.readCommit(id);
    }
    ```

  * 可重复读（REPEATABLE_READ）：一个事务在同一个事务范围内，始终看到同样的数据，避免了脏读、不可重复读，但是可能导致幻读：

    ```java
    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public User repeatableRead(Long id) {
        User user = userMapper.selectById(id);
        log.info("User-1020 is {}", user);
        try {
            log.info("another transaction doing insert User-1020...");
            Thread.sleep(30 * 1000);
            log.info("this transaction doing insert User-1020...");
            User iu = new User();
            iu.setId(1020L);
            iu.setUserName("Daemon");
            iu.setAge(19);
            userMapper.insert(iu);
        } catch (Exception e) {
            log.error("this transaction doing insert happen exception: {}", e.getMessage());
        }
        user = userMapper.selectById(id);
        log.info("User-1020 is {} again", user);
        return user;
    }

    /**
     * 读已提交事务级别-前后多（两）次读取的数据不存在，但实际存在
     *
     * curl -X GET http://localhost:8081/springboot/isolation/repeatableRead?id=1020
     * @param id
     * @return
     */
    @GetMapping("/repeatableRead")
    public User repeatableRead(@RequestParam("id") Long id) {
        return isolationService.repeatableRead(id);
    }
    ```

  * 序列化（SERIALIZABLE）：最严格的事务隔离级别，每个事务必须按照顺序执行，避免了脏读、不可重复读、幻读：

    ```java
    @Transactional(isolation = Isolation.SERIALIZABLE)
    public User serializable(Long id) {
        User user = userMapper.selectById(id);
        log.info("User-1020 is {}", user);
        try {
            log.info("another transaction doing insert User-1020...");
            Thread.sleep(10 * 1000);
            log.info("this transaction doing insert User-1020...");
            User iu = new User();
            iu.setId(1020L);
            iu.setUserName("Daemon");
            iu.setAge(19);
            userMapper.insert(iu);
        } catch (Exception e) {
            log.error("this transaction doing insert happen exception: {}", e.getMessage());
        }
        user = userMapper.selectById(id);
        log.info("User-1020 is {} again", user);
        return user;
    }

    /**
     * 序列化事务级别-前次读取数据不存在，插入成功后读取数据存在，另外的事务在等待且执行时抛出重复键的异常
     *
     * curl -X GET http://localhost:8081/springboot/isolation/serializable?id=1020
     * @param id
     * @return
     */
    @GetMapping("/serializable")
    public User serializable(@RequestParam("id") Long id) {
        return isolationService.serializable(id);
    }
    ```

> 剖析@Transactional注解的实现原理

> 项目代码

* [springboot-transactional](https://gitee.com/FSDGarden/springboot/tree/spring-transactional/)

> 参考文献

* [拜托，不要在问我@Transactional注解了](https://juejin.cn/post/6844904137927163912)
* [SpringTransaction](https://github.com/hechaoqi123/SpringTransaction/tree/master)
* [你必须懂也可以懂的@Transactional原理](https://juejin.cn/post/6968384376824561671)