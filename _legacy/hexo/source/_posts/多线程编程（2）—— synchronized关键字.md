---
title: 多线程编程（2） —— synchronized关键字
date: 2019-06-18 23:34:04
categories: 多线程编程
tags: 多线程
---
&nbsp;&nbsp;“非线程安全”指的是在多个线程对同一个对象中的实例变量进行并发访问时发生，产生的结果是“脏读”，即渠道的数据其实被更改过，“线程安全”指的是获得的实例变量的值是经过同步处理的，不会出现脏读问题。
## 1.1 方法内的变量为线程安全
&nbsp;&nbsp;如果变量是在方法内的，那么不存在“非线程安全”问题。
```java
public class HasSelfPrivateNum {
    public void add(String username) {
        int num = 0;
        if (username.equals("a")) {
            num = 100;
            System.out.println("a set over!");
        } else {
            num = 200;
            System.out.println("b set over!");
        }
        System.out.println(username + "num = " + num);
    }
}
```
&nbsp;&nbsp;变量在方法内。
```java
@RunWith(MockitoJUnitRunner.class)
public class ThreadSafeTest {

    @Test
    public void testSafe() {
        HasSelfPrivateNum num = new HasSelfPrivateNum();
        ThreadA threadA = new ThreadA(num);
        threadA.start();

        ThreadB threadB = new ThreadB(num);
        threadB.start();
    }
}          
```
---
## 1.2 实例变量非线程安全
&nbsp;&nbsp;线程访问的对象中如果有多个实例变量，则运行的结果可能出现交叉的情况。
```java
public class HasselfPrivateNum {
    private int num = 0;
    public void add(String username) {
        if (username.equals("a")) {
            num = 100;
            System.out.println("a set over!");
        } else {
            num = 200;
            System.out.println("b set over!");
        }
        System.out.println(username + " num = " + num);
    }
}

@RunWith(MockitoJUnitRunner.class)
public class ThreadSafeTest {
    @Test
    public void testSafe() {
        // 只有一个实例化对象，不同线程均可以访问
        HasSelfPrivateNum num = new HasSelfPrivateNum();
        ThreadA threadA = new ThreadA(num);
        threadA.start();

        ThreadB threadB = new ThreadB(num);
        threadB.start();
    }
}
```
---
## 1.3 多个对象多个锁
&nbsp;&nbsp;如果多个线程访问多个对象，JVM会创建多个锁，如图所示，创建了2个对象，会产生2个锁，不存在“非线程安全”问题。
```java
@RunWith(MockitoJUnitRunner.class)
public class ThreadSafeTest {

    @Test
    public void testSafe() {
        // 不同线程使用不同的实例化对象，不会有"非线程安全"问题
        HasSelfPrivateNum num = new HasSelfPrivateNum();
        HasSelfPrivateNum num1 = new HasSelfPrivateNum();

        ThreadA threadA = new ThreadA(num);
        threadA.start();

        ThreadB threadB = new ThreadB(num1);
        threadB.start();
    }
}
```
![](photos/13.png)

---
## 1.4 synchronized方法与锁对象
&nbsp;&nbsp;对于使用synchronized关键字修饰的方法，不同线程一定要“排队”，也就是A线程先执行，然后B线程再执行。
```java
@RunWith(MockitoJUnitRunner.class)
public class SyncTest {
    @Test
    public void test() {
        MyObject object = new MyObject();

        ThreadA threadA = new ThreadA(object);
        threadA.setName("A");

        ThreadB threadB = new ThreadB(object);
        threadB.setName("B");

        threadA.start();
        threadB.start();
    }
}
```
![](photos/14.png)
## 1.5 同步方法和非同步方法共存的情况
