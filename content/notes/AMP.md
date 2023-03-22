---
unsafe: true
title: AMP
url: /notes/amp/
math: true
---
<p></p>
<ul>
<li><a href="https://en.wikipedia.org/wiki/Asymmetric_multiprocessing">Asymmetric multiprocessing</a></li>
<li>Исторически первый способ организации многопроцессорности в компьютерных системах. Суть заключается в назначении разных ролей разным процессорам. Один процессор занимается вычислениями, другой обслуживает ввод и вывод и т.д..</li>
<li>Эта модель вычислений была вытеснена SMP, как более понятной</li>
<li>
С течением времени стало понятно что SMP архитектура обладает рядом серьезных ограничений<ul>
<li>сложно масштабировать из за необходимости согласования доступа к общим ресурсам (например RAM)</li>
<li>сложно сделать универсальный исполнитель, который одинаково хорошо подходит для разных типов вычислений <a href='/notes/тупик-вычислительной-техники'>[[Тупик Вычислительной Техники]]</a></li>
</ul>
</li>
<li>
SMP начала приобретать черты AMP<ul>
<li>не однородный доступ к памяти (NUMA)</li>
<li>специализация P/E ядер</li>
</ul>
</li>
</ul>