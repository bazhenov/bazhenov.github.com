---
date: 2009-01-09
url: /blog/2009/01/09/null-handling.html
title: Enhanced null handling в Java
tags: java language
layout: post
alias: /2009/01/enhanced-null-handling-java.html
---
Как показало голосование по вопросу java 7 language changes[^poll], null-handling в java - это самый большой "pain in the ass" из всех, через которые Java заставляет проходить программистов. С другой стороны то-же голосование на devoxxx по вопросу самого популярного языка под JVM, показало, что это Groovy.

![Результаты голосования][ref-poll-results]

Видимо, все те, кто привыкли к [оператору Элвиса][ref-elvis-op] и [safe-navigate][ref-self-navigate] в groovy, пришли на devoxxx и устроили флеш моб. Вобщем приветствуйте. Proposal[^proposal] определяет 2 новых оператора в языке: `null-safe` и `null-default`. Работает так же как и в groovy. Просто и понятно.

## Null-safe operator
```java
String a ... ;
String b;

// сегодня
b = a != null
	? a.substring(10, 2);
	: null;

// завтра
String b = a?.substring(10, 2);
```

## Null-default operator
```java
// сегодня
if ( name == null ) {
	name = "Anonymous";
}

// завтра
name = name ?: "Anonymous";
```

Лично я ничего против не имею. Давно пора.

[^poll]: [JDK 7 language changes - Devoxx votes!](http://www.jroller.com/scolebourne/entry/jdk_7_language_changes_devoxx)
[^proposal]: [Enhanced null handling](https://docs.google.com/View?docid=dfn5297z_3c73gwb&pli=1)

[ref-elvis-op]: http://groovy.codehaus.org/Operators#Operators-ElvisOperator%28%3F%3A%29
[ref-self-navigate]: http://groovy.codehaus.org/Operators#Operators-SafeNavigationOperator%28%3F.%29
[ref-poll-results]: http://chart.apis.google.com/chart?cht=p&chd=t:49,30,14,10,5,4,5,17&chds=0,49&chs=350x200&chl=Groovy%7CScala%7CJRuby%7CJython%7CFan%7CPHP%7CClojure%7CDon%27t+care&chp=3.14
