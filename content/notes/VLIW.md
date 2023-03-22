---
unsafe: true
title: VLIW
url: /notes/vliw/
math: true
---
<p></p>
<ul>
<li>VLIW – это алтернативный подход к задаче шедулинга инструкций в микропроцессорах <span class='missing-note'>[[µArch CPU]]</span></li>
<li>
VLIW на данный момент используется только в DSP-процессорах<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>The embedded DSP, on the other hand, has a well defined workload based on what application it’s deployed into. It has much tighter energy efficiency requirements. The developer can spend more time optimizing the application ahead of time. There isn’t as much pressure on multitasking: Any multitasking is a function of the application itself, and can usually be optimized to the processor. Static scheduling is a reasonable fit for this profile</p>
</blockquote>
</div></li>
</ul>
</li>
<li>
К причинам почему технология не прижилась на CPU общего назначения можно отнести:<ul>
<li>Оптимальный порядок выполнения инструкций в большей степени определяется готовностью данных необходимых для вычислений (<a href='/notes/memory-wall'>[[Memory Wall]]</a>). Но задержки получения данных на практике невозможно предсказать на этапе компиляции из за сложной иерархии памяти. Компилятору проще определить зависимости между инструкциями, но CPU проще определить оптимальный порядок выполнения инструкций.</li>
<li>
VLIW возможно не столько позволяет увеличить ILP, сколько повысить эффективность по питанию (за счет тривиального шедуллера в железе). Но в процессорах общего назначения скорее важна производительность.<ul>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>On a statically scheduled processor, such as the DSP I mentioned or processors like Itanium, you don’t have a hardware instruction scheduler. Or if you do, it’s a relatively simple one. You may not even have a branch predictor, or if you do, you may only use it as a prefetch, and won’t execute down the predicted path until you know it’s the correct path. In that case, you’re relying on the compiler to schedule instructions and expose instruction-level parallelism. That means pulling as much code from as many places as possible and scheduling it to use the machine’s resources, including registers</p>
</blockquote>
</div></li>
<li><div class='quote'><p class='quote-source'><span class='missing-note'>2021_11_22</span></p><blockquote>
<p>As a result, general purpose processors have all pretty much made a different tradeoff than the embedded DSP I worked with. General purpose processors have to run quite a lot of different code, spread across multiple processors, in a dynamic multitasking environment. They have strong demands on peak performance, but not so much on energy efficiency or real time predictability. Dynamic scheduling is a good fit, since the environment itself is much more dynamic</p>
</blockquote>
</div></li>
</ul>
</li>
<li>Для процессоров используемые в ПК в большей степени важна пиковая производительность и им не требуется поддерживать ее в течении длительного времени. Но это не касается например серверных CPU. В этом отношении персональные и серверные CPU должны быть спроектированы совсем по разному. При этом на них должно выполнятся одно и то же ПО. Архитектуры должны быть совместимы</li>
</ul>
</li>
</ul>
