---
title: 并发编程 —— Lock接口
date: 2020-09-14 23:46:11
categories: 并发编程
tags: Lock
---
  多个线程访问共同资源的时候，需要通过加锁来保证资源访问。java有两种通用的解决思路：
  + synchronized
    + java保留关键字
  + juc包下的lock接口
    + jdk提供
              
# lock
  