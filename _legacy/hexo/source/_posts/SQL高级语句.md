---
title: SQL高级语句
date: 2020-09-21 00:47:53
tags:
---

## 通配符
_           代替一个字符
[abc]       字符列中的任何单一字符
[^charlist] 不在字符列中的任何单一字符
[!charlist] 不在字符列中的任何单一字符

```sql
SELECT * FROM Websites WHERE name LIKE '_oogle';

SELECT * FROM Websites WHERE name LIKE 'G_o_le';

SELECT * FROM Websites WHERE name REGEXP '^[GFs]';

SELECT * FROM Websites WHERE name REGEXP '^[^A-H]';
```

## between
  BETWEEN 操作符可以用于选取介于两个值之间的数据范围内的值。这些值可以是数值、文本或者日期。