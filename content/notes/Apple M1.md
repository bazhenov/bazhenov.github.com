---
unsafe: true
title: Apple M1
url: /notes/apple-m1/
math: true
---
<p></p>
<ul>
<li>
Фото подложки<ul>
<li><img src="https://pbs.twimg.com/media/FCBl1gcWEAUOdRw.jpg" alt="" />{:height 442, :width 724}</li>
</ul>
</li>
<li>
Значимые отличия<ul>
<li>
Чип достаточно большой<ul>
<li>
M1 – 16 миллиардов<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>However, the whole chip is A LOT bigger than your typical desktop processor from AMD or Intel, AMD Gen3 Ryzen 7 has 8 cores in 5 billion transiistors, Intel core i9 somewhere between 3 and 7 billion, depending on model. Apple put down 16 billion transistors in this chip. Even at the 5nm, it’s a pretty big chip.</p>
</blockquote>
</div></li>
</ul>
</li>
<li>
M1 Pro – 33 миллиадра, M1 Max – 57 миллиардов<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_20</span></p><blockquote>
<p>The M1 Pro packs up to 10 CPU cores (8 high-performance, 2 high efficiency) and pairs it with up to 16 GPU cores. There are 33.7 billion transistors in the product and the SoC offers 200GB/s of memory bandwidth across a 256-bit memory bus. The eight high performance cores offer a total of 24MB of L2 cache, with a 192KB instruction cache and 128KB data caches. The data cache sizes for the M1 Pro and M1 Max are scaled up to match the increased core count.</p>
</blockquote>
</div></li>
</ul>
</li>
<li>
Для сравнения AMD Ryzen 7 5800H – 10 миллиардов<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>AMD is making the Ryzen 7 5800H on a 7 nm production node using 10,700 million transistors
Cache L1: 64K (per core)
Cache L2: 512K (per core)</p>
</blockquote>
</div></li>
</ul>
</li>
</ul>
</li>
<li>
<a href='/notes/гетерогенные-вычисления'>[[Гетерогенные вычисления]]</a><ul>
<li>ускорители оптимизирующих обработку видео и изображений</li>
</ul>
</li>
<li>
Декодирование инструкций<ul>
<li>8-way decoder. Для сравнения самый широкий для x86 декодер появился а GolvenCove и это 6</li>
<li>ARM64 в отличии от x86 проще декодить потому что фиксированная длинна инструкции</li>
<li>
Интересно что 8-канальный декодер считается теоретическим максимумом<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>Collectively the power consumption, complexity and gate delay costs limit the achievable superscalar speedup to roughly eight simultaneously dispatched instructions</p>
</blockquote>
</div></li>
</ul>
</li>
</ul>
</li>
<li>
Кеш<ul>
<li>существенно больше L1 и L2. Видимо это связано с тем что шина памяти шире глубже OoE-execution</li>
</ul>
</li>
<li>Один из первых процессоров на DDR5</li>
</ul>
</li>
</ul>
