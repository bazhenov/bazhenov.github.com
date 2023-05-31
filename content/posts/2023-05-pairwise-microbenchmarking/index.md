---
date: 2023-05-31
title: Paired benchmarking. How to measure performance
url: posts/paired-benchmarking
tags: [performance, statistics, rust]
---

## Introduction

In this article, I discuss the [challenges](#challenges) associated with testing algorithm performance, focusing primarily on microbenchmarks rather than overall application performance, although some principles apply to both. I provide a [brief overview of efforts to address](#addressing) these challenges and highlight some limitations we're encountering.

Subsequently, I introduce an alternative method of performance testing called [paired benchmarking](#paired), which effectively tackles some of these challenges. While paired benchmarking is a [well-known statistical technique](https://en.wikipedia.org/wiki/Paired_difference_test), as far as I am aware, it has not yet been implemented in any benchmarking tools.

Finally, I present the [experimental results](#results) and [share the Rust source code](https://github.com/bazhenov/rust-pairwise-testing) for those interested in experimenting with this concept.

## Why is benchmarking challenging? {#challenges}

Benchmarking the performance of an algorithm is a difficult task due to the need for a controlled environment. Computer systems are complex and stateful, with various interactions between their components, such as hardware and the operating system.

Achieving complete control over the system state to ensure consistent performance across benchmark runs is nearly impossible. Several factors contribute to the lack of reproducible results, including:

- CPU frequency scaling mechanisms
- CPU thermal and power limitations
- Unpredictable latencies in the memory hierarchy caused by preemptive task execution and migration between NUMA nodes
- Interruptions from the operating system
- Latencies in scheduling processes

Here are some observations I have encountered during performance benchmarking on my laptop:

1. Playing music in the background leads to a performance decrease of approximately 3-5%. It is worth noting that all benchmarks are single-threaded. Could this be attributed to scheduling latency?
2. When running the benchmark after adding a dependency to `Cargo.toml`, the performance drops by around 10%. However, with each subsequent benchmark run, the performance gradually returns to normal. My suspicion is that the active recompilation process triggered by adding the dependency puts the CPU in a state where it experiences more aggressive thermal limitations.

## How we are addressing these challenges? {#addressing}

There are several approaches we are employing to tackle these challenges, each with its drawbacks.

### Striving for tighter control

One approach involves exerting greater control over the system in which the benchmarks are executed. This includes measures such as disabling Turbo Boost and similar features, statically throttling the CPU to bypass dynamic power and thermal limitations, dedicating specific cores to the benchmark, and ensuring no other tasks are running concurrently.

While this approach can yield positive results, it is not foolproof. It is difficult to guarantee that all influencing factors remain constant, and it is not a sustainable solution in the long run. As hardware evolves, it becomes increasingly complex and intricate. Even if this method works today, it may become more challenging in the future.

### Extending benchmark duration

Another option is to run benchmarks for a longer duration. If performance fluctuates over time, providing the benchmark with more time may allow it to stabilize and reveal the true performance of the algorithm. Surprisingly, this approach can sometimes have adverse effects.

It is commonly assumed that execution times follow specific probability distributions, with normal and log-normal distributions being the most popular choices. Can you identify the distribution of observations in the graph below?

{{<image "graphs/multiple-modes.svg" >}}

I observe the presence of at least 7 distinct execution modes in the graph. Although each mode can be reasonably modeled as a probability distribution, it is important to note that the system as a whole cannot be accurately described by any single distribution. This is due to the violation of a fundamental assumption in most statistical methods: the independence of observations.

It is crucial to understand that **algorithm execution time does not follow a specific probability distribution**. Computers are dynamic and stateful systems, constantly transitioning between different modes of operation. The benchmark itself contributes to these transitions and introduces outliers. The longer the benchmark runs, the more state transitions and outliers the algorithm will encounter.

### Ignoring outliers

Regarding the issue of outliers, it is a common approach to consider ignoring them. The rationale behind this is that if performance exhibits a wide range of variation, the outliers are likely measurement errors that do not provide meaningful insights into the algorithm. However, we should exercise caution in automatically dismissing outliers. What if, for some reason, outliers only occur when a new version of the algorithm is implemented? Should we disregard them?

Instead of regarding outliers as measurement errors, we should perceive them as observations of the system in rare states that may or may not be influenced by our algorithm. If we choose to ignore outliers, we need to provide compelling reasoning for why we believe they are unrelated.

In practice, a simple approach often employed is to filter out extreme observations, such as removing the largest 1% of measurements[^rust-outliers].

### Utilizing a more robust metric

It may be worth considering the use of a different metric instead of the mean execution time. Since the mean is sensitive to outliers, we can explore metrics that are less influenced by them, such as the median[^rust-median] or the minimum value[^mean-misleads] [^accurate-benchmarks]. However, there are considerations to keep in mind when deciding which metric to report.

While the median or minimum value can be employed as performance differential metrics (which will be further discussed in the following section), it is essential to note that the numbers we present to others should be based on the mean time. Mean time holds significant importance in system design and back-of-the-envelope calculations because it directly relates to the algorithm's maximum potential throughput, which is a key optimization goal in most cases. Neither the median nor the minimum value can substitute the mean in this context.

## Two types of performance metrics

I propose the existence of two distinct types of performance metrics: integral and differential. An integral metric represents the performance that we report to others, indicating the overall capability of the algorithm (e.g., "the algorithm can decompress 8Gb/s"). As mentioned earlier, this estimate is crucial for discussions about performance and plays a significant role in design considerations. The most suitable choice for an integral metric is the mean.

However, in the day-to-day work of performance engineers and researchers, there is a need for a metric that can continually assess whether changes are improving the algorithm's speed. I refer to this as the differential metric. Typically, the differential metric is constructed by comparing a candidate algorithm with a baseline using an integral metric. For instance, if the baseline algorithm achieves a decompression rate of 8GB/s and the candidate algorithm achieves 9Gb/s, we can conclude that the candidate is an improvement.

One crucial characteristic of the differential metric is its sensitivity. Even if the new version of the algorithm is only a few percent faster, the differential metric should still indicate a change. The mean, unfortunately, lacks the necessary sensitivity. Consequently, we often resort to aggressively discarding inconvenient observations and repeatedly iterating in the hope that the mean will eventually stabilize. However, relying solely on comparing the pointwise means will not provide the desired outcome.

Instead, it is essential to construct a stable differential metric from scratch, designed to accurately capture and quantify performance changes between two algorithms.

## Paired benchmarking {#paired}

The proposed solution is to conduct paired benchmarking by executing both the baseline and candidate algorithms in a randomized order and measuring the difference in their execution times. This approach ensures that both algorithms are subject to the same system biases at any given moment, making it easier to identify meaningful differences between them. Let's consider the following benchmark run as an example:

{{< image "graphs/pair-test.svg" >}}

If we solely look at the individual execution times of the algorithms (shown as the red and green lines in the left graph), it becomes challenging to discern any noticeable difference due to the high amount of "noise." However, the variability of the difference between the candidate and baseline (shown in the right graph and blue line in the left graph) is considerably lower. This indicates that fewer iterations are needed to obtain more precise feedback.

Additionally, we observe that the execution time distribution exhibits at least two peaks or "modes." Interestingly, in one mode, the order of function execution appears to have no significant influence on runtime (as indicated by points lying on the symmetry line). However, in the other mode, the execution order does affect runtime, although the points still exhibit a symmetrical distribution.

The general algorithm for measuring performance using paired benchmarking is as follows:

1. Prepare the same input data for both the baseline and candidate algorithms.
2. Execute the baseline algorithm and measure its execution time.
3. Execute the candidate algorithm and measure its execution time.
4. Record the difference in runtime between the baseline and candidate algorithms.

These steps constitute a single run, which serves as a distinct benchmark observation. Multiple runs are then performed, with each subsequent run employing a new payload and a randomized order in which the baseline and candidate functions are executed. Randomization is necessary to account for different CPU states and cache effects.

The advantages of using paired benchmarking include:

- The difference metric is less susceptible to ephemeral biases in the system, as common-mode biases are eliminated.
- Differences in means typically have lower variance since both algorithms are tested on the same input.
- It becomes easier to identify and eliminate outliers that are not caused by algorithm changes, thereby enhancing test sensitivity.

The last point requires further clarification.

As mentioned earlier, outliers can only be eliminated if it can be demonstrated that they are not a result of the algorithm itself. When testing a single algorithm independently, it is challenging to determine this. However, when comparing two algorithms in a paired benchmark, we can establish that if outliers are not caused by the candidate algorithm, both algorithms should experience a similar number of outliers with comparable severity. We can now test this hypothesis and filter outliers only if the observations do not contain data that contradicts it.

Suppose we have the benchmarking results for two algorithms as shown in the graph below:

{{< image "graphs/outliers.svg" >}}

In the difference graph, we observe several peaks. To determine which peaks can be safely ignored, we can focus on the two most prominent ones. Since they are in opposite directions and have similar magnitudes, we can disregard them. Additionally, we may choose to ignore 3 other peaks. The likelihood of these peaks being independently distributed can be computed using a binomial distribution, resulting in a value of 37.5%. This approach provides a more conservative method for identifying and disregarding outliers.

## Experimental Results {#results}

I implemented several variants of functions to calculate the number of characters in a UTF8 encoded string using the Rust standard library. The following variants were selected:

```rust
/// Idiomatic way of calculating length of the string in Rust
fn std(s: &str) -> usize {
    s.chars().count()
}

/// Manual character counting
fn std_count(s: &str) -> usize {
    let mut l = 0;
    let mut chars = s.chars();
    while chars.next().is_some() {
        l += 1;
    }
    l
}

/// Manual character counting in reverse order
fn std_count_rev(s: &str) -> usize {
    let mut l = 0;
    let mut chars = s.chars().rev();
    while chars.next().is_some() {
        l += 1;
    }
    l
}

/// Counting only first 5000 characters
fn std_5000(s: &str) -> usize {
    s.chars().take(5000).count()
}

/// Counting only the first 4925 characters (5000 - 0.5%)
fn std_4925(s: &str) -> usize {
    s.chars().take(4925).count()
}
```

Firstly, the program checks some of the functions against themselves to ensure the integrity of the benchmarking framework. This step helps control for any potential issues or biases that may arise within the benchmarking process.

Here are the benchmarking results from my machine:

```
name                          B min C min  min ∆     B mean C mean mean ∆ mean ∆ (%)
std / std                       344   344   0.0%      478.7  468.8    0.5       0.1%
std_count / std_count          1417  1417   0.0%     2327.7 2318.8   -1.8      -0.1%
std_count_rev / std_count_rev  1418  1416  -0.1%     3630.4 4396.1   -2.4      -0.1%
std_5000 / std_4925            2111  2081  -1.4%     3606.5 3447.8  -86.6      -2.4% CHANGE DETECTED
std_count / std_count_rev      1417  1417   0.0%     2484.6 2538.3   62.6       2.5% CHANGE DETECTED
std / std_count                 260  1416 444.6%      450.7 2714.1 2199.5     488.0% CHANGE DETECTED
```

For each comparison, the following metrics are reported:

- Names of the tested functions (e.g., `std_5000 / std_4925`: `std_5000` is the baseline, `std_4925` is the candidate).
- `B min`/`C min`: Minimum execution time of the baseline and candidate functions across all observations.
- `min ∆`: The difference between the candidate and baseline in percent (negative means the candidate is faster).
- `B mean`/`C mean`: Mean execution time of the baseline and candidate functions.
- `mean ∆`: Paired difference mean in ns and % (mean of the difference of the individual observations).
- `CHANGE DETECTED` indicator is printed where the difference between means is statistically significant based on z-test.

A few observations can be made:

1. Minimum execution time is a robust metric. When used with paired tests, it converges much faster, providing stable results with just 100 iterations, compared to close to 1000 iterations without paired testing. This significantly speeds up performance tests, making them as fast as unit tests.
2. With a relatively modest number of iterations (approximately 10^4 to 10^5), this method is capable of detecting changes with an effect size of less than 1%.
3. The results of paired benchmarks are highly robust even in the presence of load in the system. Tests with a parallel dummy load (`m5sum /dev/random`) running on each physical core yield consistent results.
4. Sometimes, the minimum time metric is unable to detect a change even when it is present. For example, in the case of `std_count / std_count_rev`, the reverse iteration is several percent slower according to the mean.

To further investigate the assumption that there is a difference between forward and backward iteration, a criterion.rs benchmark was conducted to measure the "classical" pointwise difference (i.e., the difference of means). The results are as follows:

```
utf8/std_count          time:   [2.7335 µs 2.8060 µs 2.8786 µs]
utf8/std_count_rev      time:   [3.0029 µs 3.0804 µs 3.1495 µs]
```

These results confirm that backward iteration is indeed slower. However, let's examine pointwise benchmarks for `std_length_5000`/`std_length_4925`:

```
utf8/std_length_5000    time:   [3.9461 µs 4.0783 µs 4.2288 µs]
utf8/std_length_4925    time:   [3.1340 µs 3.1875 µs 3.2455 µs]
```

Based on these results, it appears reasonable to conclude that `std_length_4925` performs faster. However, the magnitude of the difference is quite large. To gain further insight, let's change the order in which the benchmarks are run:

```
utf8/std_length_4925    time:   [3.4154 µs 3.4940 µs 3.5771 µs]
                        change: [+5.3494% +8.4154% +11.806%] (p = 0.00 < 0.05)
                        Performance has regressed.
utf8/std_length_5000    time:   [3.1802 µs 3.2415 µs 3.3061 µs]
                        change: [-21.896% -18.510% -15.017%] (p = 0.00 < 0.05)
                        Performance has improved.
```

Remarkably, the results have flipped. **The function being run last tends to have an advantage**. Pointwise testing, in such nuanced circumstances, is not sensitive enough to detect meaningful differences. However, I find the results for `std_count`/`std_count_rev` more reliable since `std_count_rev` is slower despite being favored by the benchmark.

## Conclusion

Computers are intricate systems that we cannot fully control, making it challenging to achieve reproducible results when measuring algorithm performance. However, the technique of paired testing, commonly used in classical statistics, offers a solution to mitigate the influence of confounding factors on observations, thereby reducing variance. This approach is also applicable when assessing algorithm performance. By reducing variance, we can reap two key benefits:

1. **Reduced iteration count**: With lower variance, we can achieve stable results with fewer iterations. This allows for quicker iteration cycles or more extensive testing of the algorithm within the same timeframe.
2. **Improved sensitivity**: The reduced variance enhances the test's sensitivity, enabling the detection of more subtle changes in performance. This empowers us to identify and assess even nuanced improvements or deviations in the algorithm's behavior.

Incorporating paired testing into performance measurement practices offers the potential to streamline iterative processes and enhance the ability to detect and analyze performance changes effectively.

[mean-misleads]: 
[BID23]: 

[^rust-outliers]: Rust bench harness [ignores 10% of most extreme observations](https://github.com/rust-lang/rust/blob/e6e4f7ed1589e03bc2f6c5931c1a72e7947e8682/library/test/src/bench.rs#L150-L158)
[^rust-median]: Rust bench harness uses [median as the main metric](https://github.com/rust-lang/rust/blob/e6e4f7ed1589e03bc2f6c5931c1a72e7947e8682/library/test/src/bench.rs#L71-L79)
[^accurate-benchmarks]: [Accurate and efficient software microbenchmarks](https://www.youtube.com/watch?v=BFISG3LY9UQ) by Daniel Lemire
[^mean-misleads]: [The mean misleads: why the minimum is the true measure of a function’s run time](https://betterprogramming.pub/the-mean-misleads-why-the-minimum-is-the-true-measure-of-a-functions-run-time-47fa079075b0) by David Gilbertson