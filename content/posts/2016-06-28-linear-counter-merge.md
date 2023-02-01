---
date: 2016-06-28
url: /blog/2016/06/28/linear-counter-merge.html
layout: post
title: Объединение линейных счётчиков
math: true
---

Линейный счётчик — это очень [простой алгоритм оценки мощности множества](/blog/2012/12/12/linear-counter.html). Тем не менее, у него есть одна не очевидная и очень полезная особенность. Побитовая сумма (логическое ИЛИ) двух линейных счётчиков позволяет оценить мощность объединения двух множеств.

Например, у вас есть два множества $A$ и $B$, а также их линейные счётчики $A'$, $B'$. Тогда:

$$L_{A' | B'} \approx |A \cup B|$$

где $L_x$ – функция оценки линейного счётчика.

Это свойство крайне полезно для оценки, например, количества уникальных посетителей того или иного ресурса за произвольный промежуток времени.

## Use case: сколько пользователей заходило на сайт за последние 6 часов

Допустим, вы хотите рассчитать сколько уникальных пользователей пользовалось сайтом за последние 6 часов. При этом оценка должна обновлятся раз в минуту. В зависимости от количества посещений эта задача вполне может решатся и в лоб. Взять логи за последние 6 часов, посчитать количество уникальных посетителей, повторить. Но если посещений много, то в одну минуту можно или не уложится. Или утилизировать полностью ресурсы машины без особого запаса на рост.

Линейные счётчики позволяют решить эту задачу гораздо более эффективно по ресурсам, уложившись в очень скромные аппаратные бюджеты.

Для этого достаточно хранить 360 поминутных счётчиков (6 часов = 6 * 60 минут), раз в минуту вытесяня один старый счётчик и добавляя один новый (пустой). В этот новый счётчик мы и регистрируем текущие посещения. В итоге мы имеем поминутную оценку количества уникальных посетителей ресурса.

Теперь пользуясь свойством объединения линейных счётчиков достаточно побитово сложить 360 счётчиков между собой и расчитать оценку количества уникальных посетителей за последние 6 часов.

## Точность оценки при объединении счётчиков

Приятная особенность — точность оценки остаётся прежней. Операция объединения счётчиков неотличима от операции индексации объекта в счётчик. Вы можете выразить процедуру индексации через процедуру объединения счётчиков и наоборот. На самом деле это одна и та же операция. Это следует из простого факта, — дизьюкция является коммутативной и ассоциативной операцией.

Следовательно, исходная оценка точности линейного счётчика относится к обоим операциям.

Этот метод использования линейных счётчиков позволяет довольно сильно снизить аппаратный бюджет некоторых решений. И, как следствие, воплотить в жизнь идеи, которые ранее считались экономически нецелсообразными.