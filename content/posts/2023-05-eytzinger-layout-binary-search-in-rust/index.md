---
date: 2023-05-01
title: Fast(er) binary search in Rust
url: posts/faster-binary-search-in-Rust
draft: true
tags: [performance, rust, cpu]
---

## Introducton

Binary search is quite fast algorithm.  Due to its exponenential nature it allows to crunch through gigabytes of sorted data in no time. But there are two problems which makes it somewhat "indigestible" for moder CPUs:

- predictability of instruction flow;
- predictability of memory access.

At each step binary search splits dataset in two parts and jumps to one of those parts based on a midpoint value. It's hard for CPU to predict which parts of presumably large array will be accessed on the next iteration. So naturally binary search produces a lot of cache misses which stalls CPU pipeline resuling in poor instruction per clock performance.

So let's try to find a way to fix those problems. But first, let's measure [`slice::binary_search()`](https://doc.rust-lang.org/std/primitive.slice.html#method.binary_search) performance as a baseline using `Vec<u32>` of different sizes.

{{< image "std.svg" >}}

{{< notice note "Test platform" >}}
- Intel Core i7-1068NG7 CPU @ 2.30GHz
- 32Gb LPDDR4X 3733 MHz
- Darwin Kernel Version 22.4.0

You can reproduce this experiment using [published code][sources].
{{</ notice >}}

Practically speaking performance of binary search start to drop when the dataset become larger than the size of on-core cache size (L2) which in my case is 512KB or 128K `u32` elements.

## Eytzinger Layout

One of the ways we can address memory access predictability problem is the Eytzinger layout. It's a method of storing sorted data in such a way that elements at the same tree depth are stored together. Let's illustrate the idea.

{{< image "eytzinger-layout.jpg" >}}

Array starts with the tree root (depth=0), followed by all the elements at depth 1, than depth=2 and so on. Using this layout tree siblings are always stored together in memory, which means less cache misses.

This layout requires array preprocessing, so it appropriate when underlying array is fixed or at least changes infrequently. I will not dive deep into algorithm of constructing such an array. You can check [sources][sources] or read [1].

Although it might seem quite complex, navigating eytzinger layout array is simple if you store all your elements starting from index 1 (first element is a dummy). You just update index to `idx = 2 * idx` if you wanna go left or `idx = 2 * idx + 1` if right:

```rust
pub fn binary_search(data: &[u32], value: u32) -> usize {
  let mut idx = 1;
  while idx < data.len() {
    let el = data[idx];
    if el == value {
      return idx;
    }
    idx = 2 * idx + usize::from(el < value);
  }
  0
}
```

We don't need to maintain array search boundaries anymore!

Let's benchmark our code against standart binary search.

{{< image "eytzinger.svg" >}}

Intresting. When dataset small enough to fit in cache Eytzinger is able to provide significant performance gain. But everything changes when we hit the main memory.

## Branchless Eytzinger implementatation

Let's try another idea. But first let's check the [assembly of our eytzinger implementation](https://godbolt.org/z/qW37aMYf6)

```asm{linenos=inline,hl_lines=["6-12"]}
example::eytzinger_binary_search:
        cmp     rsi, 2
        jb      .LBB0_4
        mov     eax, 1
.LBB0_2:
        cmp     dword ptr [rdi + 4*rax], edx
        je      .LBB0_5
        setb    cl
        movzx   ecx, cl
        lea     rax, [rcx + 2*rax]
        cmp     rax, rsi
        jb      .LBB0_2
.LBB0_4:
        xor     eax, eax
.LBB0_5:
        ret
```

Basically our loop body (highlighted lines 6-12) contails two branches:

- `cmp`+`jb` on lines 11-12 are the loop invariant – `idx < data.len()`;
- `cmp`+`je` on lines 6-7 checking if we found target element, if we do we jump to `.LBB0_5` where the return from a function is executed

We can not do anything about first branch, but the second one actually can be eliminated.

{{< notice note "Why you should even try to eliminate branches?" >}}

CPUs are hundreds of cycles away from the main memory, so they are trying to predict which code will be executed in near future and prefetch all needed instructions and operands. Branch instructions are [control hazard](https://www.cs.umd.edu/~meesh/411/CA-online/chapter/handling-control-hazards/index.html) to the CPU pipeline. They introduce uncertainty about where code execution will flow next. Almost all CPUs except most simple ones will speculate if branch ahead will be taken or not. But CPU will hit perfromance penalty in form of [pipeline stall](https://en.wikipedia.org/wiki/Pipeline_stall) if misprediction happens. So it's nice when we can get rid of branches in the first place.
{{</ notice >}}

This is where exponential nature of binary search becomes handy. In practice it can be more beneficial not to check if we found target element in a loop body and traverse the whole tree down to leafs anyway. Yes there will be some extra iterations, but quite a few because of binary search is `O(log n)` in complexity.

```rust
pub fn binary_search_branchless(data: &[u32], value: u32) -> usize {
  let mut idx = 1;
  while idx < data.len() {
    let el = data[idx];
    idx = 2 * idx + usize::from(el < value);
  }
  idx >>= idx.trailing_ones() + 1;
  usize::from(data[idx] == target) * idx
}
```

Last 2 lines of code worth some attention. Here we decode index of a found element.

### How the found element index is decoded?

It might be not obvious how the following code is decoding index of target element (if any). So let's look closer:

```rust
idx >> (idx.trailing_ones() + 1)
usize::from(data[idx] == target) * idx
```

Decoding code rely on the following facts:

1. following two expressions are equivalent
   ```rust
   // arithmetic index update
   idx = 2 * idx + usize::from(el < value);
   // binary operation index update
   idx = (idx << 1) | usize::from(el < value);
   ```
   From this you can conclude that `idx` can been interpreted as a binary tree traversal history where each bit is 1 if we took a right turn and 0 if a left one. For example, value 19 (`0001_0011`) after 5 iterations means that the sequence of turns was: RLLRR.
2. if we found target element we will make a left turn `usize::from(el < value) == 0`
3. when we make a left turn (in context of `el == value`) we ended up in part of a tree where all elements less that target. Therefore all subsequent turns will be right turns.

(1) means that you can revert effect of arbitrary number of iterations just by shifting `idx` right. (3) means that the required number of iterations you need to revert is the number of trailing ones in an `idx`. Off by one is to cancel out the iteration where target element was found (we're intrested in value `idx` before iteration completed).

After this manipulation `idx` will point at the least element in the array **greater or equal to `target` or zero if there is no such element**. Now we only need to check this element against target. We can do it with following branched code:

```rust
// naive solution
if data[idx] == target { idx } else { 0 }

// branchless solution
usize::from(data[idx] == target) * idx
```

Let's benchmark branchless version of code against previous implementations

{{< image "eytzinger-branchless.svg" >}}

Branchless eytzinger is faster than branchy one, still on large datasets standart binary search outperform both of those algorithms.

## Branchless Eytzinger with memory prefetch

Although Eytzinger layout memory access is very predictable it seems like on a large arrays memory access is still dominating overall running time. The slope of eytzinger layout changed drastically when algorithm forced to go to the main memory.

Let's add software memory prefetch. We know that next iteration will always require consequent elements of an array: `2 * idx` or `2 * idx + 1`. This allows us to instruct CPU about data we will need on the next iteration:

```rust{hl_lines=["4-7"]}
pub fn binary_search_branchless(data: &[u32], value: u32) -> usize {
  let mut idx = 1;
  while idx < data.len() {
    unsafe {
      let prefetch = data.get_unchecked(2 * idx);
      _mm_prefetch::<_MM_HINT_T0>(ptr::addr_of!(prefetch) as *const i8);
    }
    let el = data[idx];
    idx = 2 * idx + usize::from(el < value);
  }
  idx >>= idx.trailing_ones() + 1;
  usize::from(data[idx] == target) * idx
}
```

{{< notice note "Is it safe?" >}}
Formally no, but in practice... kind of, becuase we never dereference prefetched address. `_mm_prefetch()` is an intrinsic for `PREFETCHh` instruction which by documentation

> is merely a hint and does not affect program behavior

In case of invalid address and TLB errors prefetch instruction will ignore address. This allows to do prefetch unconditionally even on the last iteration when `2 * idx` is pointing after the end of an array 🫣.
{{</ notice >}}

{{< image "eytzinger-branchless-prefetch.svg" >}}

Memory prefetching indeed helps eytzinger layout to perform faster that standart binary search across wide range of array sizes.

## Common pitfals when performance testing

- benchmark should produce enough memory pressure to be representative in terms of memory access. 1 in a 1000 problem
- benchmark should produce diverse enough lookups to stress branch predictor. first thousands elements if an array

## Conclusion

Branchless Eytzinger layout is a great option if the data you are searching over are fixed and can be preprocesses to accommodiate faster memory access layout. Because it respects charactecrisitcs of modern CPUs it is basically one of the fastest ways to search in the sorted data when implemented correctly.

Additionally there are some further ideas like S trees ([4]) or mixed layout ([2]) you could try if you're looking for the best binary search.

## Related links

1. [Eytzinger Binary Search](https://algorithmica.org/en/eytzinger), Algorithmica
2. [Array Layouts for Comparison-based Searching](https://arxiv.org/pdf/1509.05053v1.pdf) Paul-Virak Khuong
and Pat Morin
3. [Control Hazard](https://www.cs.umd.edu/~meesh/411/CA-online/chapter/handling-control-hazards/index.html), Computer Architecture, Dr Ranjani Parthasarathi
4. [Optimizing Binary Search](https://github.com/CppCon/CppCon2022/blob/main/Presentations/binary-search-cppcon.pdf), CppCon 2022, Sergey Slotin

[sources]: https://github.com/bazhenov/eytzinger-layout