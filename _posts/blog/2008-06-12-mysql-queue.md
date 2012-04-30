---
title: MySQL Queue
layout: post
tags: messaging mysql
---
Случайно нашел интерестное программное решение. [Q4M][ref-q4m] — иммитация сервера очереди сообщений посредством MySQL сервера (начиная с версии 5.1). Написано что *fast*, *robust* и *flexible* (интерестно, бывает что-нибудь одно?). Однако, дозволяются условные выборки из очереди, несмотря на то, что в limitations указано, - индексы при этом не используются.

Вообще, довольно трудно представить себе где бы могла мне пригодится такая очередь сообщений. Cуществует куча бесплатных специализированных решений, которые создавались специально для обработки очередей сообщений. Взять хотя бы [ActiveMQ][ref-activemq] или [JBossMQ][ref-jbossmq]. Поддержка транзакционности, оптимизирована для быстрой вставки (в принципе, как и любая другая MQ система), поддержка практически всех популярных скриптовых языков посредством [STOMP][ref-stomp], встроенный [message router][ref-camel], поддержка репликации, поддержка forward on demand bridge и куча еще чего. Учитывая то, что MQ системы обычно применяются либо при интеграции приложений либо в целях масштабируемости приложений (что говорит о больших обьемах данных), непонятно зачем нужно решение подобное `Q4M`. Рано или поздно вы упретесь в пропускную способность sql-сервера по чтению, добавите slave серверов, а затем упретесь в ту же пропускную способность, но уже по записи. И тут уже никакая репликация не спасет.

Справедливости ради надо отметить, что `Q4M` предоставлят возможности, которых в других mq системах нет. Например, conditional consuming и join'ы очередей с обыкновенными таблицами! В принципе, кому-то может пригодится. Ebay, если верить некоторым источникам[^ebay-mq], использует самописный messaging стек, который поддерживает conditional consuming. Это упрощает использование очереди, да и EIP[^eip] была бы раза в два тоньше. Вот только за все приходится платить, и за удобство использования тоже. Особенно, когда за очередью прячется реляционная база данных. В данном случае платить придется производительностью, failover'ом и масштабирумостью.

[^eip]: [Enterprise Integration Patterns: Designing, Building, and Deploying Messaging Solutions](http://www.enterpriseintegrationpatterns.com/)
[^ebay-mq]: [Architecture You Always Wondered About: Lessons Learned at Qcon](http://natishalom.typepad.com/nati_shaloms_blog/2007/11/architecture-yo.html)

[ref-q4m]: http://q4m.31tools.com/
[ref-activemq]: http://activemq.apache.org/
[ref-jbossmq]: http://community.jboss.org/wiki/JBossMQ
[ref-camel]: http://activemq.apache.org/camel/
[ref-stomp]: http://stomp.codehaus.org/
[ref-ebay-mq]: http://natishalom.typepad.com/nati_shaloms_blog/2007/11/architecture-yo.html

