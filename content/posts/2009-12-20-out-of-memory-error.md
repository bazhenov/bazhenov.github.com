---
date: 2009-12-20
url: /blog/2009/12/20/out-of-memory-error.html
title: Диагностика OutOfMemoryError подручными средствами
layout: post
tags: [java, cache, jdk]
alias: /2009/12/outofmemoryerror.html
---
Один мой коллега является адептом философии "дефолтных настроек". Эта философия пропагандирует следующий подход: не пытайтесь менять environment под свои нужды, — просто научитесь пользоваться стандартным environment'ом.

Несмотря на то что сам по себе этот подход довольно спорен, в нем есть свои плюсы. Умение решать задачи штатными средствами особенно выручает когда необходимо быстро продиагностировать какую-то проблему, а у вас под рукой нет настроенного environment'а. Например, вы временно работаете за другой машиной, или географически отдалены от вашего милого сердцу, прекрасно настроенного environment'а. Поэтому, я считаю, очень важно уметь диагностировать типовые проблемные ситуации пользуясь только штатными утилитами. Так что давайте посмотрим как мы можем диагностировать memory leak'и в java, когда у вас под рукой нет ничего кроме JDK.

Итак, в логах вы нашли `OutOfMemoryError`. Что делать? Во-первых, надо уяснить чего делать не надо. _Ни в коем случае не надо перезапускать процесс_. Сделав это вы потеряете весь heap приложения, а в нашем случае heap — это единственная улика, которая может натолкнуть вас на причины OOM. Вам надо сделать heap dump. Это позволит понять кто занимает память, а также почему эта память не была конкретно высвобождена garbage collector'ом.

Самый простой способ сделать dump — это использовать утилиту jmap из пакета JDK.

	$ jmap -dump:format=b,file=heap-dump.hprof $PID

Вот теперь, когда вы сделали dump, вы можете смело возвращать систему к жизни и перезапускать JVM, если это требуется.

Перед доставкой dump'а на вашу машину советую его пережать, так как heap dump'ы очень хорошо жмутся. Когда dump будет на вашей машине возникает вопрос. А каким образом вообще понять что там у "не внутря"?

С последними версиями JDK поставляется приложение [VisualVM][ref-visualvm], которое содержит в себе в том числе и memory profiler. Загружаем heap dump в VisualVM и открываем вкладку "Classes".

![Распределение памяти по классам](/images/out-of-memory-error/fig1.png)

На этой вкладе мы видим распределение памяти в dump'е по классам объектов. В данном случае большего всего памяти занимает тип `char[]`. Видимо кто-то хранит много строчек в памяти. Кто же это?

Дважды щелкаем на типе и переходим в instance view. Здесь мы видим все экземпляры данного типа, а также кто на них ссылается, а следственно и то, почему GC их не собрал. Просматриваем несколько экземпляров.

![Путь к GC-root'ам](/images/out-of-memory-error/fig2.png)

В моем случае большинство ссылок на строку удерживается базой данных H2 при помощи soft reference. Немного погуглив можно узнать, что [H2][ref-h2] использует soft reference для хранения кеша базы данных. Отличительной особенностью soft ссылок является то, что JVM собирает их только тогда, когда ей не хватает памяти (перед генерацией OOM). Это делает soft ссылки довольно удобным механизмом для различного рода кешей. Тем не менее JVM не гарантирует что она успеет собрать все soft ссылки перед генерацией exception'а. Что, судя по всему, и происходит в моем случае.

Также стоит отметить, что VisualVM может сам находить ближайших GC root, удерживающий данный instance от garbage collector'а.

![Show Nearest GC root](/images/out-of-memory-error/fig3.png)

Это избавляет вас от необходимости сайгаком прыгать по дереву referent'ов в поисках ближайшего GC root'а.

## Auto dump

Иногда бывает так, что причиной `OutOfMemoryError` служит не нехватка памяти, а другие причины. Например, если JVM видит, что она тратит большую часть процессорного времени на сборку мусора, а не на выполнение собственно приложения, она генерирует следующий exception.

	java.lang.OutOfMemoryError: GC overhead limit exceeded

В зависимости от того как написано приложение оно может остаться живо, и даже продолжать выполнять свои функции. Причем уже через несколько минут heap может быть чистенький и без лишнего мусора (GC не зря жрал так много процессорного времени, и в конце концов собрал весь мусор).

Отладка затрудняется, — у вас нет heap'а, хоть на кофейной гуще гадай. В этом случае, стоит перезапустить приложение с ключом `-XX:-HeapDumpOnOutOfMemoryError`. Это заставит JVM сделать heap dump автоматически перед тем как кидать в бедное приложение OOM'ом. После следующего подобного инцидента у вас появится пища для размышлений.

## Runtime статистика

Часто бывает так, что у программиста появляется теория относительно того, почему возникает memory leak. Например, зная список последних изменений кодовой базы, можно предположить что проблема локализована в каком-то конкретном участке системы. В этом случае, вам снова может помочь jmap. Эта утилита позволяет просмотреть количество экземпляров и занимаемую ими память по типам.

	$ jmap -histo $PID | egrep "(#instances|---|java.util.LinkedList)"
	 num     #instances         #bytes  class name
	----------------------------------------------
	 110:           506          20240  java.util.LinkedList$Entry
	 166:           220           8800  java.util.LinkedList
	1021:             5            240  java.util.LinkedList$ListItr

Вы также можете легко посчитать суммарную память занимаемую типами определенного пакета.

	$ jmap -histo $PID | grep "org.netbeans" | awk '{SUM += $3} END {print SUM/1024 "K"}'
	1745.28K

Да пребудет с вами сила дефолтных настроек.

[ref-visualvm]: https://visualvm.dev.java.net/
[ref-h2]: http://www.h2database.com/html/main.html
