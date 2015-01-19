---
title: Groovy Remote Shell
layout: post
tags: groovy java
alias: /2009/04/groovy-remote-shell.html
---
Я работаю в довольно интенсивно развивающемся проекте. Мы много эксперементируем с разными инструментами. Иногда приходится инструменты разрабатывать самим.

Последний инструментарий, который мне пришлось реализовать самому — это удаленный groovy shell. Если вы незнакомы с [groovy][ref-groovy], то скажу, что это динамический язык работающий на JVM.

Задачей было разработать инструментарий, который бы позволил удаленно дергать некий служебный функционал внутри приложения (запускать переиндексацию, менять настройки thread pool'ов, удалять или создавать обьекты в БД и т.д.). Сначала для этих целей мы использовали JMX. Оказалось слишком сложно и неудобно. Решили сделать удаленный shell, который бы позволял выполнять groovy код в адресном пространстве приложения, что называется, на лету. Что может быть проще, чем получить ссылку на фасад, загрузить пару обьектов и послать им пару сообщений, – прямой канал с приложением в обход всех web-интерфейсов.

Взяв за основу [groovysh][ref-groovysh] (стандартный интерпретирующий shell идущий в поставке с groovy) и поигравшись немного с Input/OutputStream, я написал клиента который работает с удаленно запущенной инстанцией groovysh так же, как если бы он был запущен локально (работает автодополнение по tab, command history и т.д.).

![Groovy shell](/images/groovy-remote-shell/sample.png)
{:.image .photo}

[ref-groovy]: http://groovy.codehaus.org/
[ref-groovysh]: http://groovy.codehaus.org/Groovy+Shell