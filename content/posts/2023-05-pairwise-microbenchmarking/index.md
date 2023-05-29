---
date: 2023-05-28
title: Paired benchmarking. How to measure performance properly.
url: posts/paired-benchmarking
tags: [performance, rust, cpu, statistics]
draft: true
---

## Introduction

In this article, I'll start from what are the challenges when testing the performance of the algorithms. I will be talking about microbenchmarks mainly, not the application performance as a whole. Although some of the principles are applied there also. I'll give a brief overview of how we are trying to overcome those challenges and what some of the drawbacks are.

Next, I'll describe an alternative way of performance testing – paired benchmarking and how it solves some of those challenges. Although it's a well-known technique in statistics, to the best of my knowledge this is not implemented in any benchmarking tools yet.

Finally, I'll describe the experimental result as well as provide Rust source code for experimenting with this idea.

## Why benchmarking is hard?

To test the performance of an algorithm in a reproducible way we need a controlled environment. Unfortunately, computer systems are complex, stateful systems with intricate interactions between their components like hardware and operating system.

It's almost impossible to fully control the state of the system so that each run of the benchmark will experience the same performance. Some of the factors preventing reproducible results:

- CPU frequency scaling facilities;
- CPU thermal and power limiting;
- Unpredictable memory hierarchy latencies due to preemptive task execution and migration between NUMA nodes;
- OS interrupts;
- scheduling latencies;

## How we are trying to overcome those challenges?

There are several ways and each one of them is coming with its own drawbacks.

### Trying harder to control

One of the ways is trying harder to control each and every aspect of the system where benchmarks are executed. Disabling Turbo Boost and its alternatives, throttling CPU statically so it won't be subject to dynamic power and thermal limiting, pinning benchmark to dedicated cores, checking no other tasks are executing in the system, and so on.

It definitely can bring fruit, but it's not a robust solution. It's hard to make sure nothing has changed and all the factors that could possibly influence the performance are still under control. It's also not a robust solution in the long term. Hardware evolution history if teaches us anything, is that it become more and more complex and convoluted. Even if you can get away with this method today, it will be harder tomorrow.

### Run benchmark longer

Another option is to run benchmarks longer. If the performance is varying with time, let's give the benchmark more time to settle down on a true performance of the algorithm. Surprisingly, sometimes this method makes things worse.

It is assumed that execution time follows some particular probability distribution with the most popular choices being normal and log-normal. Can you name the distribution of observations on the following graph?

{{<image "graphs/multiple-modes.svg" >}}

I see at least 7 different modes of execution here. Although each mode can be somewhat adequately modeled as a probability distribution, the system as a whole can't be. The basic assumption of almost all statistical methods – observation independence – is clearly violated.

**Algorithm execution time does not follow any probability distribution**. Computers are stateful systems, which are frequently changing modes of operation. And the benchmark itself is one of the reasons why it happens. The longer your benchmark is running the more state transitions and outliers your algorithm will experience.

### Ignoring outliers

Speaking of outliers. Another popular option is to ignore outliers. It goes like this. If the performance is varying in a wide range it must be outliers found a way into the performance measurements. Outliers are thought of as some kind of measurement error that must be ignored because they're not conveying any useful information about the algorithm. In practice, we can't be sure about that. What if for whatever reason outliers are only registered when the new version of the algorithm is in place? Should we ignore them?

We must think of outliers not as measurement errors, but as an observation of the system in a rare state which may or may not be influenced by our algorithm. We need to provide some argument why we think they are not connected if we want to ignore them.

But usually, some simple form of filtrating extreme observations is employed, like removing 1% largest measurements.

### Using a more robust metric

Maybe we should take a chance with some metric other than mean execution time? Mean is not robust in the presence of the outliers, so let's use metric which is not influenced by them so much, like median or minimum value. Apart from what I've already said in the previous section about ignoring outliers, there is another problem with that.

Although median or min value can be used as a performance differential metric (more on that term in the following section), the numbers we are reporting to other people must be based on mean time. Mean time is very important in the system design and back-of-the-envelope calculations because it is directly connected to the algorithm's maximum possible throughput, which is what we optimize for in most cases. Not median nor minimum values can substitute the mean in that regard.

## Two kinds of the performance metrics

I believe, there should be two kinds of performance metrics: integral and differential. An integral metric is what we are reporting to others (the algorithm is able to decompress 30Gb/s). As I've already mentioned, this estimate is very important when discussing performance and designing with performance in mind. An integral metric should describe the performance of the algorithm as a whole. The most viable choice here is the mean.

But in day-to-day work performance engineers and researchers need a metric to continuously check if changes are making the algorithm faster. I call this metric – differential. Usually, this metric is constructed by comparing candidate and baseline algorithms using an integral metric. The baseline algorithm is decompressing 30GB/s and the candidate is able to do 32Gb/s, thus the candidate is better.

One very important quality of the differential metric is sensitivity. Sometimes the new version of the algorithm is several percent faster, and still differential metric should indicate a change. The problem is mean just doesn't sensitive enough. As a result, we are aggressively removing non-convenient observations and flooring the pedal of a number of iterations in the hope that the mean will stabilize. It will not.

Instead, we need to construct the stable differential metric from scratch.

## Paired benchmarking

The proposed solution is to execute baseline and candidate algorithms in randomized order and measure the difference in their execution time. This way both algorithms are subject to the same biases the system has at the moment. This way it's easier to highlight meaningful differences between algorithms. Consider the following benchmark run.

{{< image "graphs/pair-test.svg" >}}

If we look only at algorithm execution time independently (left graph red and green lines) it is hard to see if there is any difference it's too much "noise". But the variability of the difference between the candidate and test is much lower! Which means fewer iterations and faster feedback. Secondly, on the right plot, we see that execution time distribution has at least two peaks or two "modes". And it seems like in one mode the order in which functions are executed is not important (all points are on the symmetry line), while in the other it influences the function run time. But still, the points are placed symmetrically.

The general algorithm for measuring is as follows:

1. the same input data for both algorithms is prepared;
1. the baseline algorithm is called an execution time is measured;
1. the candidate algorithm is called an execution time is measured;
1. the difference in the run time of the baseline and candidate algorithm is recorded.

Those steps constitute the single run which is a distinct benchmark observation. Then several runs are performed each next one has a new payload and randomized order in which baseline and candidate functions are executed. Randomization is needed to compensate for different CPU states and cache effects.

Advantages of such a way of testing:

- difference metric is less susceptible to the ephemeral biases of the system because common-mode biases are eliminated.
- a difference in the means usually has a lower variance, because both algorithms are tested on the same input.
- it is easier to identify outliers that are not caused by the changes in the algorithm and eliminate them, further improving test sensitivity.

The last point needs additional clarification.

As I said earlier we can only eliminate outliers if we can demonstrate they are not created by the algorithm itself. When testing the single algorithm we have no meaningful way of doing so. But when we test 2 algorithms agains each other we know that if the outliers are not caused by the candidate algorithm then both algorithms should experience the similar amount of outliers with similar severity. Now we can test this hypothesis and filter outliers only if observations doesn't contain data which rejects it.

Suppose following benchmarking results of 2 algorithms.

{{< image "graphs/outliers.svg" >}}

On the diff. graph we can see some peaks. We can safely ignore 2 most prominent, because they are in opposite directions and have similar magnitude. Maybe we can ignore 5 of them. The likelihood those peaks are independently distributed can easily be computed using binomial distribution. In this this case it is 37.5%. This provides more conservative way of ignoring outliers.


## Empirical results

I choose several variants of calculating the number of characters in UTF8 encoded string. Following functions were implemented using Rust standart library:

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

/// Counting only first 4925 characters (5000 - 0.5%)
fn std_4925(s: &str) -> usize {
    s.chars().take(4925).count()
}
```

First test program check some of the functions against themseves to control for any issues with benchmarking framework. Then functions compared to each other.

Here is the results from my machine:

```
name                          B min C min  min ∆     B mean C mean mean ∆ mean ∆ (%)
std / std                       344   344   0.0%      478.7  468.8    0.5       0.1%
std_count / std_count          1417  1417   0.0%     2327.7 2318.8   -1.8      -0.1%
std_count_rev / std_count_rev  1418  1416  -0.1%     3630.4 4396.1   -2.4      -0.1%
std_5000 / std_4925            2111  2081  -1.4%     3606.5 3447.8  -86.6      -2.4% CHANGE DETECTED
std_count / std_count_rev      1417  1417   0.0%     2484.6 2538.3   62.6       2.5% CHANGE DETECTED
std / std_count                 260  1416 444.6%      450.7 2714.1 2199.5     488.0% CHANGE DETECTED
```

For each comparison following data is reported:

- names of the tested function (eg. `std_5000 / std_4925`: `std_5000` is baseline, `std_4925` is candidate);
- `B min`/`C min` – minimum execution time of baseline and candidate functions across all observaions;
- `min ∆` - difference between candidate and baseline in percents (negative mean candidate is faster);
- `B mean`/`C mean` - mean execution time of baseline and candidate functions;
- `mean ∆` - paired difference mean in ns. and % (eg. mean of the difference of the individual observations);
- `CHANGE DETECTED` indicator is printed where the difference between means are statistically significant based on z-test.

Several things should be noted

1. minimum execution time is indeed quite robust metrics. When used with paired tests it converges so fast that 100 iterations is enough to provide stable results. Without paired testing it is close to 1000. This is mindblowing! It makes performance tests as fast as unit tests!
1. with large number of iterations this method is able to detect changes with effect less than 1%;
1. the results of paired benchmarks are very robust in the presense of the load in the system. I ran tests with dummy load in parallel (`m5sum /dev/random`) on each physical core and results are the same;
1. sometime minimum time is not able to detect a change when it present. See: `std_count / std_count_rev`, reverse iteration is several percent slower according to the mean

Let's check last assumption. Maybe mean is lying to us, and there is no difference between forward and backward iteration? I wrote criterion benchmark which measures "classical" pointwise difference (eg. difference of means) – here is the results.

```
utf8/std_count          time:   [2.7335 µs 2.8060 µs 2.8786 µs]
utf8/std_count_rev      time:   [3.0029 µs 3.0804 µs 3.1495 µs]
```

Nope, backward iteration is indeed slower.

## Conclusion

Computers are complex system which we can not control fully. Sometimes it's very hard to get reproducible results when measuring algorithm performance. Paired testing is a known technique used in classical statistic. It allows to reduce the effects of confounders on observations thus reducing variance. This works also when measuring algorithm performance. Reduced variance can be spent on two improvements:

- reduce number of iterations to produce stable results. This allows to iterate quicker or, alternativley, test the algorithm more extensivly in the same amount of time.
- improve test sensitivity to detect more nuanced changes.