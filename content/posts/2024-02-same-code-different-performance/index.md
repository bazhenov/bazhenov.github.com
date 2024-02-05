---
date: 2024-02-02
draft: true
title: Same code different performance
---

## Introduction

> Good weather is specific weather. Conclusion: there is no such thing as good weather.
>
> _Pilot's proverb_

TLDR: the same code placed on the different addresses can have different performance

As software developers, we assume that any specific code has some particular performance which is an intrinsic part of that code and the hardware it is running on. It puts us in the position of control when modifying code and trying different optimizations to influence the performance. Although it is mostly true, in this article I want to describe phenomena that will probably undermine the perceived degree of control that we think we have over the performance. Also, I will provide an [sandbox][github] for demonstrating this phenomenon using Rust programming language.

## Why care?

As you will see shortly different code aligning can easily give up to a 5-20% performance difference (in some extreme cases I saw a 30% difference) which you as a software developer can easily attribute to a change you've made in the source code. It might be the case that observed performance gains have nothing to do with it. You need to be cautious and cross-check the results to prevent false optimizations and so-called performance swings. I'll show you how you can easily check if this is the case.

I got some peculiar cases when a simple change of function definition order in a source code brings a 10% improvement in performance. Of course, this improvement is long gone after some other irrelevant change to a source code.

## Experimental setup

Let's put the hardware to work, shall we? We will start with simple iterative factorial computation:

```rust
fn factorial(mut n: u64) -> u64 {
    let mut m = 1u64;
    while n > 1 {
        m = m.saturating_mul(n);
        n -= 1;
    }
    m
}
```

Then we need a macro that will produce a given amount of `nop` instructions at the compile time. So if compiled with `NOP_COUNT=3` it will produce:

```rust
std::arch::asm! { "nop", "nop", "nop" }
```

We will use this macro inside a loop in the `factorial()` function to be able to control the loop length precisely.

```rust
fn factorial(mut n: u64) -> u64 {
    let mut m = 1u64;
    while n > 1 {
        m = m.saturating_mul(n);
        n -= 1;
        unsafe {
		    __asm_nops();
        }
    }
    m
}
```

Now we need a way to produce 10 identical factorial functions. There are some [shenanigans][shenanigans] required to get the job done, but in the end, we got an executable with 10 duplicates of the same function:

```console
$ nm target/release/same-code-different-performance | grep factorial | rustfilt
0000000000009b00 t same_code_different_performance::factorial_1
0000000000009b50 t same_code_different_performance::factorial_2
0000000000009ba0 t same_code_different_performance::factorial_3
0000000000009bf0 t same_code_different_performance::factorial_4
0000000000009c40 t same_code_different_performance::factorial_5
0000000000009c90 t same_code_different_performance::factorial_6
0000000000009ce0 t same_code_different_performance::factorial_7
0000000000009d30 t same_code_different_performance::factorial_8
0000000000009d80 t same_code_different_performance::factorial_9
0000000000009dd0 t same_code_different_performance::factorial_10
```

Note that all odd `factorial_*()` functions have even addresses. It will become important later.

Then I wrote a simple function that measures the performance of those 10 duplicates and produces an output with the difference between the slowest and fastest function.

In theory, there should be no difference in the performance of those functions. In the end, they are identical and differ only in function address (you can easily make sure it is the case using `objdump --disassemble-symbols=[FN] [BIN]`).

## Empirical data

As a performance measure, I took the performance discrepancy between the slowest and fastest functions out of 10 duplicates (max-min). Here are the results from AWS `c1.medium` instance (`Xeon E5 2651`).

```console
$ ./run
NOP_COUNT=1 max-min difference = 4
NOP_COUNT=2 max-min difference = 3
NOP_COUNT=3 max-min difference = 2
NOP_COUNT=4 max-min difference = 3
NOP_COUNT=5 max-min difference = 4
NOP_COUNT=6 max-min difference = 2
NOP_COUNT=7 max-min difference = 2
NOP_COUNT=8 max-min difference = 3
NOP_COUNT=9 max-min difference = 2
NOP_COUNT=10 max-min difference = 6
NOP_COUNT=11 max-min difference = 3
NOP_COUNT=12 max-min difference = 4
NOP_COUNT=13 max-min difference = 3
NOP_COUNT=14 max-min difference = 59
NOP_COUNT=15 max-min difference = 59
NOP_COUNT=16 max-min difference = 39
NOP_COUNT=17 max-min difference = 31
NOP_COUNT=18 max-min difference = 57
NOP_COUNT=19 max-min difference = 57
NOP_COUNT=20 max-min difference = 39
NOP_COUNT=21 max-min difference = 30
NOP_COUNT=22 max-min difference = 56
NOP_COUNT=23 max-min difference = 57
NOP_COUNT=24 max-min difference = 45
NOP_COUNT=25 max-min difference = 45
NOP_COUNT=26 max-min difference = 46
NOP_COUNT=27 max-min difference = 46
NOP_COUNT=28 max-min difference = 52
NOP_COUNT=29 max-min difference = 1
NOP_COUNT=30 max-min difference = 2
NOP_COUNT=31 max-min difference = 2
NOP_COUNT=32 max-min difference = 3
NOP_COUNT=33 max-min difference = 2
NOP_COUNT=34 max-min difference = 3
NOP_COUNT=35 max-min difference = 3
NOP_COUNT=36 max-min difference = 3
NOP_COUNT=37 max-min difference = 3
NOP_COUNT=38 max-min difference = 3
NOP_COUNT=39 max-min difference = 3
NOP_COUNT=40 max-min difference = 3
NOP_COUNT=41 max-min difference = 3
NOP_COUNT=42 max-min difference = 3
NOP_COUNT=43 max-min difference = 3
NOP_COUNT=44 max-min difference = 43
NOP_COUNT=45 max-min difference = 47
NOP_COUNT=46 max-min difference = 46
NOP_COUNT=47 max-min difference = 46
NOP_COUNT=48 max-min difference = 46
NOP_COUNT=49 max-min difference = 46
NOP_COUNT=50 max-min difference = 46
```

![](./fig1.svg)

Here we can see that usually discrepancy is under 5ns, but for nop counts 14-28 and 44-50 there are 30-50ns per invocation difference between the slowest and fastest function.

Let's see what is the difference between individual functions for some particular value of NOP_COUNT=14.

```console
$ NOP_COUNT=14 cargo run --release 2>&1 | sort
factorial_1 = 356
factorial_2 = 302
factorial_3 = 354
factorial_4 = 297
factorial_5 = 356
factorial_6 = 302
factorial_7 = 354
factorial_8 = 297
factorial_9 = 356
factorial_10 = 302
```

![](./fig2.svg)

Do yoy recognize the pattern? Basically all even functions are fast and all odd are slow. Those results are very stable and reproducible also with the criterion[^criterion]:

```console
$ NOP_COUNT=14 cargo run --release --features=criterion -- --bench
factorials/1  time:   [351.05 ns 351.14 ns 351.23 ns]
factorials/2  time:   [295.58 ns 295.69 ns 295.92 ns]
factorials/3  time:   [348.73 ns 348.80 ns 348.88 ns]
factorials/4  time:   [295.61 ns 295.66 ns 295.71 ns]
factorials/5  time:   [350.39 ns 350.44 ns 350.51 ns]
factorials/6  time:   [295.16 ns 295.25 ns 295.38 ns]
factorials/7  time:   [348.79 ns 348.85 ns 348.91 ns]
factorials/8  time:   [295.70 ns 295.79 ns 295.92 ns]
factorials/9  time:   [351.01 ns 351.07 ns 351.14 ns]
factorials/10 time:   [295.17 ns 295.22 ns 295.26 ns]
```

## Why it happens?

Short answer: machine code produced by the compiler has suboptimal aligning in terms of micro-op caching (DSB thrashing).

I have no intent or expertise to do a deep dive into Intel microarchitectures here, so I'll try to explain the issue in simple terms as I understand it. If you are interested in more information about the decoding pipeline of Intel CPUs I highly recommend reading [1, 5, 6, 7, 8]

~~Modern computing is based around von Neumann architecture where code is data in a RAM. So it is not so surprising that alignment issues also manifest themselves for code access. But the most important reason is that one of the factors modern CPUs are optimized for, as a means of improving overall performance, is instruction level parallelism (ILP). It puts a lot of pressure on the CPU frontend to be able to predict, prefetch, and decode instructions long before they need to be executed.~~

Modern CPUs doesn't execute instructions directly, but decode them to μops first (micro-ops). Intel mainstream CPUs in particular have 3 components that are responsible for decodding and handling μops: MITE[^mite], LSD[^lsd] and DSB[^dsb].

While MITE is a de-facto instruction decoder, LSD and DSB can collectively be called a μop-cache. It holds the results of decoding individual instructions into micro-operations that are executed by the CPU. When μop is delivered by LSD/DSB, the decoder engine (MITE) doesn't need to fetch and decode instructions again. This is very effective for hot loops and frequently called functions.

Both LSD and DSB have their limitations in terms of the number of μops being stored, the type of those μops, and also alignment of the instructions[^dsb-algo]. For example on Sandy Bridge DSB is organized as 32 sets of 8 ways, each way can store up to 6 μops summing up to 1536 μops total [5]. But, and here is important part, only 3 ways are allowed per each 32 bytes aligned window of instructions. Now lets see at the machine code of `factorial_1` and `factorial_2` functions

![](./layout.png)

Here green instructions are part of a hot loop and red lines denotes 32 bytes boundaries. We can clearly see that in case of `factorial_1` all hot loop is fit inside single 32 byte window therefore on Sandy Bridge it only can use 3 ways in DSB which limits it to 18 cached uops. `factorial_2` hot loop on the other hand is crossing 32 byte window and is not subject to this limitation. By default compiler trying to align every function to a 16 bytes so both functions takes 5 32 byte windows. Consequently situation repeats for `factorial_3` and `factorial_4`.

## How to check if aligning is the issue?

You can force the Rust compiler to align functions and code blocks on a given address boundary and check if the performance swing will go away.

Compile benchmarks with the LLVM flags `-align-all-functions=6` and `-align-all-nofallthru-blocks=6`. It will force compiler to align all functions and code blocks to 64-byte boundary (2<sup>6</sup>) [4].

```console
$ RUSTFLAGS="-C llvm-args=-align-all-functions=6 -C llvm-args=-align-all-nofallthru-blocks=6" cargo bench
```

If an alignment is the issue the difference in performance should dissappear.

Alternatively, if you have a platform with access to the hardware performance counters you can check value of `DSB_MISS_PS` and `DSB2MITE_SWITCHES.PENALTY_CYCLES` counters for both variants [1].

## Should I always align to get better performance?

As a general rule – no. There is no guarantee of aligned code to be faster. It might in some cases, but most likely the other way around – code aligned on a larger boundaries will itself be larger therefore slower. Factorial-case is a demonstration of that[^factorial-reason] – aligned code is slower.

Having said that – there are some recommendation in [6]:

> When executing code from the Decoded ICache, direct branches that are mostly taken should have all their instruction bytes in a 64B cache line and nearer the end of that cache line. Their targets should be at or near the beginning of a 64B cache line.
> 
> When executing code from the legacy decode pipeline, direct branches that are mostly taken should have all their instruction bytes in a 16B aligned chunk of memory and nearer the end of that 16B aligned chunk. Their targets should be at or near the beginning of a 16B aligned chunk of memory.

Not much if you ask me.

## Should I always align to get stable results in CI?

I have no experience using those flags in CI, so take my words with a grain of salt.

Strictly speaking aligning should provide more stable performance, but only when the underlying code is the same. But if two benchmarked functions are different, compiler may generate different layout for each one of them and changing alignment requirements will be additional degree of freedom

## What to do with this kind of issue?

Unfortunately, I don't have a simple answer for that. Even the languages considered system-level are providing rudimentary means of control of this behavior, if any. And if they would it wouldn't change a thing. The optimization target, in this case, is not a platform (eg. x86), but the microarchitecture (eg. Alder Lake), which is too much of a hassle for most of the software I believe.

## Is the problem limited to x86?

I don't have a definitive answer for that yet. I have found some cases on the M3 Max chip that can be plausibly explained by inefficient micro-op caching. But I can not claim this is the real reason. I don't know of any alternatives to micro-op performance counters on the macOS/aarch64 platform that are required to confirm this hypothesis.

## Conclusion

Code aligning can influence the performance of the software on the order of magnitude of up to 20%. We as software developers don't have full control over it. Even if we would that wouldn't change much. The vast diversity of microarchitectures out there makes those kind of optimizations not practical. But at least we can be aware of this factor and don't chase the performance ghosts.

## Links

1. https://easyperf.net/blog/2018/01/18/Code_alignment_issues
2. https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf
3. https://xuanwo.io/2023/04-rust-std-fs-slower-than-python/
4. https://easyperf.net/blog/2018/01/25/Code_alignment_options_in_llvm
5. https://www.youtube.com/watch?v=IX16gcX4vDQ
6. Intel® 64 and IA-32 Architectures Optimization Reference Manual. Section 3.4.2.5: Optimization for Decoded ICache
7. The microarchitecture of Intel, AMD, and VIA CPUs. Sections 11.2-11.4
8. https://en.wikichip.org/wiki/intel/microarchitectures/sandy_bridge_(client)#Decoding

[github]: https://github.com/bazhenov/same-code-different-performance
[shenanigans]: https://github.com/bazhenov/same-code-different-performance/blob/6dba5f2bfad3c90f8cdc22d5c6855f1276b98011/src/main.rs#L14-L15

[^dsb-algo]: There are materials describing quite precise rules on how DSB caching works in the Sandy Bridge–Sky Lake microarchitecture span [5, 7, 8], but I'm unaware of any information regarding Ice Lake and later microarchitectures.
[^mite]: Macro Instruction Translation Engine

[^lsd]: Loop Stream Detector or Loopback Buffer
[^dsb]: Decoded ICache or Decoded Stream Buffer
[^criterion]: Although results are reproducible with criterion, it might require different value of `NOP_COUNT`. This is because changing dependencies as well as code will change binary layout hence changing the number of nops required to reproduce the issue.
[^factorial-reason]: although I should note that in this case aligned code is slower because I'm intentionally using single byte nops to generate a lot of μops in a loop. If you use multibyte nops the effect will goes away.