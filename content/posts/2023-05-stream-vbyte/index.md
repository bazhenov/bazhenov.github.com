---
date: 2023-05-20
draft: true
title: "Compress-a-Palooza: Unpacking 5 Billion Varints in only 4 Billion CPU Cycles"
url: posts/rust-stream-vbyte-varint-decoding
tags: [performance, rust, cpu]
---

## Introduction

Varint is a well-known technique for compressing integer streams. It boils down to the very simple idea – sometimes it's just more efficient to encode a number not as a fixed-size binary representation, but as a variable-length one. It allows stripping all the leading zeros from the binary number, thus reducing its representation size. It's working better the smaller the number is being encoded.

In this article, I give a brief introduction and motivation for varint encoding. Then I describe [Stream VByte][vbyte] format which allows fully vectorized decoding using SSE instructions and some of my findings when I [implemented this algorithm in Rust][github]. The implementation provides encoding as well as decoding primitives and allows to read data from RAM as well as from disk.

Algorithm was tested on several platforms:

| CPU             | Base Freq. (GHz)  | Turbo Freq. (GHz) | Result (GElem/s) |
|-----------------|------------------:|------------------:|-----------------:|
| Xeon E3-1245 v5 |               3.5 | 3.9               | 5.0              |
| Core i7-1068NG7 |               2.3 | 4.1               | 5.5              |


The decoding speed is 0.75 CPU cycles per integer on average.

## Motivation

Varint compression is widespread and is used in a variety of places:

- in the serialization formats for more effective state transfer representation (for example, [Protobuf][protobuf]);
- in database engines (for example, SQLite uses it in a [BTree page format][sqlite]);
- search engines are heavily using it for compressing the document lists containing ids of the documents where some word is presented (so-called, posting lists);
- one can argue that UTF8 is a varint encoding. Although, it's a special one, handcrafted for backward compatibility with ASCII text binary representation.

Being a very successful technique it suffers from one particular problem – low decoding speed. To understand why, we need to understand how classical varint encoding is working.

## Scalar varint

Usually, varint is reserving the most significant bit of each byte to represent if this byte is a continuation of the previous one. The rest of the bits are carrying the number itself.

- numbers that can fit in 7 bits (without leading zero bits of course) are encoded as `0xxxxxxx`;
- 14 bits are encoded as `0xxxxxxx 1xxxxxxx`
- 24 bits – `0xxxxxxx 1xxxxxxx 1xxxxxxx` and so on...
- 32-bit numbers in this scheme will be encoded as 5 bytes `0000xxxx 1xxxxxxx 1xxxxxxx 1xxxxxxx 1xxxxxxx`

The problem is it introduces strong data dependency in the format. You can start decoding the next number only after you decoded the previous one because you need to know the offset where the next number starts in the byte stream. It prevents executing instructions in parallel on modern CPUs.

## Stream VByte

Varints decoding can be vectorized in several ways, including [varint-G8IU][patent] format patented by Google. One elegant solution, in my opinion, is the [Stream VByte][vbyte] format proposed by Daniel Lemirea, Nathan Kurzb, and Christoph Ruppc.

It goes like this. Let's separate length information and numbers data into different independent streams, so we can decode a bunch of numbers in parallel.

Here is a simple observation: for `u32` there are 4 possible lengths of the number in bytes. They can be represented using 2 bits (`00` - length 1, `11` - length 4). Using 1 byte we can encode the length of 4 `u32`'s. Let's call this byte – control byte. The sequence of control bytes we call the control stream. The second stream called the data stream contains the bytes of the compressed varint numbers laid out sequentially one after the other without any 7-bit shenanigans.

Let's look at the example. Suppose we encode 4 numbers: `0x00000011`, `0x00002222`, `0x00333333`, and `0x44444444`. In encoded format, they will look like this:

```
CONTROL STREAM:
   0x27    <- 00_01_10_11 – lengths 1, 2, 3 and 4 respectively

DATA STREAM:
   0x11, 0x22, 0x22, 0x33, 0x33,
   0x33, 0x44, 0x44, 0x44, 0x44
```

Now we can read a single control byte, decode lengths of 4 `u32` numbers and decode them one by one. This is already some improvement over the original scalar decode implementation. But we can do better. Much better. We can decode all 4 numbers in 1 CPU instruction!

If you think about it, all we need to do is to insert some zeros in the correct places to align numbers properly.

```
  [[ 0x00,    0x00,    0x00 ]], 0x11,
  [[ 0x00,    0x00 ]], 0x22,    0x22,
  [[ 0x00 ]], 0x33,    0x33,    0x33,
     0x44,    0x44,    0x44,    0x44
```

And there is instruction for that.

[IMAGE]

### PSHUFB SSE instruction

Actually, it can do a lot more than that. It allows you to permute or zero out bytes in the 16-byte register in any possible way.

`PSHUFB` takes 2 16-byte registers (`__m128`): input and a mask. And producing 16-byte register output. Each byte in the output is controlled by the corresponding byte in the mask register. There are two possible variants:

- if the most significant bit of the byte in the mask register is set – then the corresponding byte in output will be zero
- if MSB is not set, then 4 lower bits address the byte in the input register which will be copied to the output.

```
  Byte offsets:          0        1        2        3        4  ...
                  ┌────────┬────────┬────────┬────────┬────────┬───┐
Input Register:   │   0x03 │   0x15 │   0x22 │   0x19 │   0x08 │...│
                  └────▲───┴────────┴────▲───┴────▲───┴────▲───┴───┘
                       │        ┌────────┘        │        │
                       │        │        ┌─────────────────┘
                       │        │        │        │
                       └───────────────────────────────────┐
                                │        │        │        │
                  ┌────────┬────┴───┬────┴───┬────┴───┬────┴───┬───┐
  Mask Register:  │   0x80 │   0x02 │   0x04 │   0x03 │   0x00 │...│
                  ├────────┼────────┼────────┼────────┼────────┼───┤
Output Register:  │   0x00 │   0x22 │   0x08 │   0x19 │   0x03 │...│
                  └────────┴────────┴────────┴────────┴────────┴───┘
```

When decoding 4 numbers in parallel we need to provide a mask that will place all the number bytes on their corresponding places in the output register. This way we can decode 4 `u32` numbers in one CPU instruction.

### How to create mask?

The neat part about this algorithm is that there is no need to compute the masks at runtime. There are only 256 possible masks that cover all the possible length variants of 4 encoded numbers. So masks can be precomputed at compile time in the array and can be easily accessed using a control byte as an index in the array. This is where Rust's `const fn` is very handy.

## Implementation details

Ok, more to the [Rust implementation][github]. To use SIMD intrinsics we will need nightly. SSE decode kernel is very simple.

```rust{linenos=inline}
type u32x4 = [u32; 4];

const MASKS: [(u32x4, u8); 256] = ...

fn simd_decode(input: *const u8, control_word: *const u8, output: *mut u32x4) -> u8 {
  unsafe {
    let (ref mask, encoded_len) = MASKS[*control_word as usize];
    let mask = _mm_loadu_si128(mask.as_ptr().cast());
    let input = _mm_loadu_si128(input.cast());
    let answer = _mm_shuffle_epi8(input, mask);
    _mm_storeu_si128(output.cast(), answer);

    encoded_len
  }
}
```

 - Line 3. Reading shuffle mask and encoded length from the statically precomputed array;
 - Lines 4-5. Loading input and masks into `__m128i` registers. It's important to note that all loads and stores must be unaligned, hence `storeu`/`loadu`. If you try to load an unaligned address using `_mm_load_si128` intrinsic you may get a segmentation violation error.
 - Line 6. Restoring proper boundaries of 4 `u32` numbers;
 - Line 7. Storing numbers in the result buffer.
 - Line 9. Returning the number of consumed bytes from the data stream. The data stream will have to advance this amount of bytes next iteration.

Now we can use this kernel to decode an arbitrary number of integers:

```rust
pub struct DecodeCursor {
  elements_left: usize,
  control_stream: *const u8,
  data_stream: *const u8,
}

fn decode(&mut self, buffer: &mut [u32]) -> io::Result<usize> {
  /// Number of decoded elements per iteration
  const DECODE_WIDTH: usize = 4;
  assert!(
    buffer.len() >= DECODE_WIDTH,
    "Buffer should be at least {} elements long",
    DECODE_WIDTH
  );
  if self.elements_left == 0 && self.refill()? == 0 {
    return Ok(0);
  }

  let mut iterations = buffer.len() / DECODE_WIDTH;
  iterations = iterations.min((self.elements_left + DECODE_WIDTH - 1) / DECODE_WIDTH);
  let decoded = iterations * DECODE_WIDTH;

  let mut data_stream = self.data_stream;
  let mut control_stream = self.control_stream;
  let mut buffer = buffer.as_mut_ptr() as *mut u32x4;

  for _ in 0..iterations {
    let encoded_len = simd_decode(data_stream, control_stream, buffer);
    data_stream = data_stream.wrapping_add(encoded_len as usize);
    buffer = buffer.wrapping_add(1);
    control_stream = control_stream.wrapping_add(1);
  }

  self.control_stream = control_stream;
  self.data_stream = data_stream;
  let decoded = decoded.min(self.elements_left);
  self.elements_left -= decoded;
  Ok(decoded)
}
```

As you can see this code heavily relay on pointers. There is a very good reason for this – performance.

## Performance Considerations

The first implementation I wrote was able to decode only around 500 million integers per second. The order of magnitude is slower than the CPU is capable of! There are some tricks you need to implement to utilize the CPU more effectively. Now I will try to explain what you need to pay attention to.

### Use correct intrinsics

When first implementing the decode kernel I used `_mm_loadu_epi8()` and not `_mm_loadu_si128()`. It turns out that `_mm_loadu_epi8()` is part of AVX512, not SSE ISA. But the program never failed, it passed all the tests. Rust library contains retrofit implementations which are used if the target CPU doesn't support some particular instruction. As you might guess, they are not nearly as fast.

**Lesson 1**: check if the intrinsic you are using is supported on the target CPU.

### Check if slice indexing is a problem

The next problem is slice indexing produces a lot of branch instructions. When indexing slices compiler is forced to check slice boundaries each time the slice is accessed. Suppose the following code:

```rust
pub fn foo(x: &[i32]) -> i32 {
    x[5]
}
```

it translates to the [following assembly][assembly-example]:

```asm
example::foo:
  push    rax
  cmp     rsi, 6
  jb      .LBB0_2
  mov     eax, dword ptr [rdi + 20]
  pop     rcx
  ret
.LBB0_2:
  lea     rdx, [rip + .L__unnamed_1]
  mov     edi, 5
  call    qword ptr [rip + core::panicking::panic_bounds_check@GOTPCREL]
  ud2
```

Here we can see the first thing compiler is doing is checking slice bounds (`cmp rsi, 6`). If it's below 6, `core::panicking::panic_bounds_check()` is called. It is a safe thing to do for the compiler, no doubt about that. But all those conditional jumps are hurting performance a lot. So in tightly optimized loops, it's better to replace slice indexing with something more efficient.

The question is what it should be replaced with? The first thing that comes to mind is `iter()`, but I can't come up with elegant coding using Rust iterators. Mainly because the data stream should be advanced with a different number of bytes in each iteration. Another option is `slice::get_unchecked()`, but I would strongly advocate against it.

The better approach, in this case, is to use pointer arithmetics in a way that saves as much safety as possible. Most of the operations of the pointers are safe by themselves, but you can end up with SIGSEGV when dereferencing them.

But as always, first, you should check if this is a problem in the first place. Consider the code I show you earlier:

```rust
const MASKS: [(u32x4, u8); 256] = ...

fn simd_decode(input: *const u8, control_word: *const u8, output: *mut u32x4) -> u8 {
  unsafe {
    let (ref mask, encoded_len) = MASKS[*control_word as usize];
    ...
  }
}
```

Here compiler can produce assembly without any additional checks because the compiler knows the following facts:

 - `MASKS` is an array of size 256;
 - `*control_world` is strictly less than 256 (`u8`).

**Lesson 2**: slice access often implies a branching which can be harmful. When optimizing code in the tight loops look for a way to replace slice indexing with the most safe alternative possible. But only after you're sure slice indexing is a problem. The most obvious alternative is `iter()`.


### Check your loops

Even after all those optimizations performance was around 2.5 billion integers per second. The thing that really speeds things up is loop unrolling. It's the same story as in [How fast can you count to 16 in Rust?]({{< ref "/posts/2023-04-counting-to-16-in-rust" >}}), you should try to minimize the number of branches per unit of work done. Nudge the compiler a little bit to perform loop unrolling.

```rust
const UNROLL_FACTOR: usize = 8;
while iterations_left >= UNROLL_FACTOR {
  for _ in 0..UNROLL_FACTOR {
    let encoded_len = simd_decode(data_stream, control_stream, buffer);
    data_stream = data_stream.wrapping_add(encoded_len as usize);
    buffer = buffer.wrapping_add(1);
    control_stream = control_stream.wrapping_add(1);
  }

  iterations_left -= UNROLL_FACTOR;
}
```

Now, I'm about to show you a very long assembly which this source translates into. Pay attention not to the individual instructions, but that it doesn't have any branching.

```asm
movzbl              (%rsi), %eax
leaq                (%rax,%rax,4), %rax
movzbl              0x10(%r11,%rax,4), %r12d
vmovdqu             (%r8), %xmm0
vpshufb             (%r11,%rax,4), %xmm0, %xmm0
vmovdqu             %xmm0, (%rbx,%r13,4)
leaq                (%r8,%r12), %rax
addq                %r12, %rdx
movzbl              0x1(%rsi), %ecx
leaq                (%rcx,%rcx,4), %rcx
movzbl              0x10(%r11,%rcx,4), %r15d
vmovdqu             (%r8,%r12), %xmm0
vpshufb             (%r11,%rcx,4), %xmm0, %xmm0
vmovdqu             %xmm0, 0x10(%rbx,%r13,4)
movzbl              0x2(%rsi), %ecx
leaq                (%rcx,%rcx,4), %rcx
movzbl              0x10(%r11,%rcx,4), %r8d
vmovdqu             (%r15,%rax), %xmm0
addq                %r15, %rax
vpshufb             (%r11,%rcx,4), %xmm0, %xmm0
vmovdqu             %xmm0, 0x20(%rbx,%r13,4)
addq                %r8, %r15
addq                %r15, %rdx
movzbl              0x3(%rsi), %ecx
leaq                (%rcx,%rcx,4), %rcx
movzbl              0x10(%r11,%rcx,4), %r15d
vmovdqu             (%r8,%rax), %xmm0
vpshufb             (%r11,%rcx,4), %xmm0, %xmm0
vmovdqu             %xmm0, 0x30(%rbx,%r13,4)
addq                $0x4, %rsi
addq                %r15, %r8
addq                %rax, %r8
addq                %r15, %rdx
leaq                0x10(%r13), %rax
addq                $-0x4, %r9
cmpq                $0x4, %r9
```

Isn't it a beauty? The whole inner loop is implemented as one long instruction highway, if you will, with no exit lanes or splits. Only arithmetics and vector operations of different kinds. Future instructions and memory accesses are easily predictable. The CPU can prefetch all needed data in time. It really helps to achieve high performance in this particular case.

And the result is 5.5 billion integers per second, which is quite remarkable for a 4.1GHz CPU if you ask me.

```
$ cargo bench -q --bench decode
decode/u32              time:   [89.660 µs 90.267 µs 90.930 µs]
                        thrpt:  [5.4988 Gelem/s 5.5391 Gelem/s 5.5767 Gelem/s]
                 change:
                        time:   [-1.0102% +0.5065% +2.2278%] (p = 0.54 > 0.05)
                        thrpt:  [-2.1792% -0.5040% +1.0205%]
                        No change in performance detected.
Found 8 outliers among 100 measurements (8.00%)
  6 (6.00%) high mild
  2 (2.00%) high severe
```

## Further optimizations

Some additional improvements can be done on top of this code which I'm looking forward to trying

- Aligning. This will allow us to get rid of some unaligned loads in the kernel. On an x86 platform, this is unlikely to give great benefit due to the intrinsically strong memory model. As far as I understand it makes more sense on ARM. But still, I wonder how much benefit it brings on x86.
- right now the length of encoded quadruplets is memoized the same way the masks do. But it is possible to compute the length of the file using some bit of trickery. But it pays off only when you are decoding not a single control word, but 4 of them at a time (as a `u32`).

## Conclusion

Varint is a simple, powerful, and widespread compression algorithm. Without this type of compression fast search engines like Apache Lucene or Tantivy would be impossible. Memory bandwidth is quickly becoming a bottleneck when you work with uncompressed data. But in its naive implementation varint is not able to saturate modern CPUs because of data dependencies. Stream VByte is solving that issue separating length and data information, which allows to read both streams independently thus pipelining the decoding algorithm.

[protobuf]: https://protobuf.dev/programming-guides/encoding/#varints
[sqlite]: https://www.sqlite.org/fileformat.html
[patent]: https://patents.google.com/patent/WO2012116086A1/en
[vbyte]: https://arxiv.org/abs/1709.08990
[github]: https://github.com/bazhenov/stream-vbyte
[assembly-example]: https://godbolt.org/z/8a3roYcTP