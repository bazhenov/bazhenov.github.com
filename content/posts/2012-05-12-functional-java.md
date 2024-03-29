---
date: 2012-05-12
url: /blog/2012/05/12/functional-java.html
title: Особенности функциональщины в Java
layout: post
tags: [java, programming, guava]
---
Некоторое время назад мне довелось участвовать в одном из подпроектов целью которого было извлечение упоминаний об автомобилях из произвольного текста с использованием экспертной информации. Это задачу в простонародье называют парсингом :). Так или иначе, этот класс задач имеет свою специфику связанную с относительно большим количеством различных операций над коллекциями. Связано это с необходимостью проверки различных гипотез относительно содержимого анализируемого текста. Оперирование над коллекциями это сильная сторона функциональных языков к которым Java конечно же не относится.

## Императивный подход

Классический императивный подход к оперированию коллекциями заключается в написании кода выполняющего обход и обработку каждого элемента коллекции. Типичный map в императивном стиле выглядит следующим образом:

```java
	List<String> result = new ArrayList<String>();
	for (Position p : autocomplete.suggest(q)) {
		result.add(p.getTitle());
	}
```

Не так уж и плохо. Но когда подобную операцию надо выполнять несколько раз в пределах одного метода, `for`'ы начинают мозолить глаз.

## Guava спешит на помощь

Мы используем [guava][ref-guava] (бывшая google collections) для упрощения оперирования коллекциями. Guava предоставляет массу функциональных примитивов для работы с коллекциями. Несмотря на излишний синтаксический шум, в Java можно применять элементы функционального программирования. Правда не без ограничений. Давайте посмотрим на вышеприведенный пример переписанный с использованием guava.

```java
List<String> result = transform(autocomplete.suggest(q), new Function<Position, String>() {
 	@Override
 	public String apply(final Position input) {
		return input.getTitle();
 	}
});
```

Если честно, то стало еще хуже. Если раньше у нас был простой и понятный `for`-цикл, то сейчас мешанина из ключевых слов и названий типов. На сегодняшний день это пожалуй самое сильное ограничение Java — _объявлять предикаты по месту проблематично из-за синтаксиса анонимных классов_. Поэтому мы пошли на следующее ухищрение.

## Вынос предикатов и map-функций

Если вы писали в функциональном стиле, то может замечали что существенный процент всех функций передаваемых в `filter`/`map` являются чистыми функциями (без состояния) и не используют замыкание. Поэтому мы решили вынести их в виде статических членов класса к которым они относятся. Это позволяет определить их один раз в рамках класса к которому они привязаны и использовать в любом месте кодовой базы.

Например, вышеприведенный пример мы переписываем следующим образом:

```java
class Position {

	public static final Function<Position, String> retrieveName = new Function<Position, String>() {
		@Override
		public String apply(final Position input) {
			return input.getTitle();
		}
	};
}
```

Тогда клиент сводится к следующему коду:

```java
List<String> result = transform(autocomplete.suggest(q), retrieveName);
```

что уже довольно вменяемо. В случае если функция обладает состоянием мы делаем для нее статическую фабрику в классе к которому она относится.

```java
class Span {
	
	public static Function<Span, String> chopFromText(final String text) {
		checkNotNull(text);
		return new Function<Span, String>() {
			@Override
			public String apply(Span input) {
				return input.cutFrom(text);
			}
		};
	}
	
	public String cutFrom(String string) {
		return string.substring(start, end);
	}
}
```

при этом клиент выглядит похожим образом:

```java
List<Span> spans = asList(new Span(0, 5), new Span(6, 2), new Span(9, 3));
List<String> words = transform(spans, chopFromText("Hello to you!"));
// words -> ["Hello", "to", "you"]
```

Этот подход работает благодаря тому что предикаты и map-функции принимают ровно один аргумент по типу которого можно определить к какому классу относить эту функцию. Таким образом, всякий раз когда вам нужен предикат на тип `Position` вы знаете что его надо искать именно в классе `Position`.

## Постскриптум

Вы никогда не получите от Java экспрессивности присущей функциональным и тем более динамическим языкам. Поэтому в некотором отношении это конечно полумера. Но сделать свою жизнь немного проще используя элементы функционального программирования все же можно. И я считаю нужно.

Ну а Java программистам которые незнакомы с guava, я настоятельно советую обратить внимание на эту библиотеку. Она содержит массу вспомогательных классов и статических методов для решения типовых задач возникающий в ежедневной практике. Ее описание с легкостью может занять целый пост, настолько обширен ее функционал.

[ref-guava]: http://code.google.com/p/guava-libraries/
