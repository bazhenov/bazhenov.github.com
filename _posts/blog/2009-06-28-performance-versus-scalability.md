---
title: Perfomance vs. scalability
layout: post
tags: concurrency perfomance scalability
alias: /2009/06/perfomance-vs-scalability_28.html
---
Иногда встречаюсь c непониманием того, что такое производительность, а что такое масштабируемость. Почему-то некоторые люди считают, что это одно и то же.

С производительностью все более менее понятно. Это мера скорости работы системы. Запрос поступает в систему и через некоторое время система генерирует ответ. Это время (которое иногда называют latency) и является мерой производительности системы. Для интернет-приложений время получения ответа клиентом может быть значительно больше, чем время генерации ответа на стороне сервера (потери в канале, необходимость загрузки дополнительных статических ресурсов и т.д). Обычно эти издержки не учитываются при оценке производительности, хотя надо признать, они могут очень сильно влиять на user experience работы с приложением.

С масштабируемостью все немного сложнее . Если производительность это ответ на вопрос "как быстро?", то масштабирумость — на вопрос "как много?". Как много пользователей одновременно могут пользоваться ресурсом? Как много данных может быть в базе данных прежде чем она перестанет справляется с нагрузкой?

Иначе говоря, оптимизация под производительность подразумевает делать ту же работу используя меньше ресурсов. Под масштабируемость — используя больше ресурсов, делать пропорционально больший объем работы.

Это может показаться странным, но оптимизация под масштабируемость нередко приводит к худшей производительности. С точки зрения производительности наверное нет ничего лучше чем sql-вызовы прямо в шаблоне (зачем тратить лишнее время на вызовы полиморфных методов, да?). Но для того чтобы хорошо масштабироваться по объему данных в БД, необходимо уметь "пилить" нагрузку между серверами. А для этого требуется гибкий механизм диспетчеризации обращений к базе данных (ORM, ActiveRecord, DataMapper, DAO или что там у вас). Нам нужен некий промежуточный слой, который бы абстрагировал клиента от знания где именно (на каком сервере) лежат данные, которые он запрашивает. В зависимости от специфики реализации такие слои могут добавлять существенный overhead к latency ответа. И все это делается только ради того чтобы быть больше, а не быстрее (на самом деле делается гораздо больше, это всего лишь частный пример), потому что в большинстве случаев *быть большим выгоднее, чем быть быстрым*.

Только не поймите меня неправильно, я не хочу сказать, что быть быстрым не надо. Пользователи не будут ходить на ваш ресурс если страницы будут открываться по 10 секунд. Что я хочу сказать, так это то, что *ваши пользователи не будут платить вам больше, если страницы вашего ресурса будут открываться не 0.2 секунды, а 0.1*. Но если у вас будет в два раза больше пользователей...