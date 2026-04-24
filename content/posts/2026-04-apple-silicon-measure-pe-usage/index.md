---
date: 2026-04-24
draft: true
url: /posts/apple-silicon-measure-pe-usage
title: "The Two Thread IDs of macOS: Measuring P/E Core Usage on Apple Silicon"
layout: post
tags: [macos]
---

## Introduction

I needed a straightforward way to check programmatically how much time a process spends on P-cores vs E-cores. There's no high-level API for it, at least not that I know of – and yet this information matters whenever you care about consistent performance on Apple Silicon.

I ran into this while working on [Tango.rs](https://github.com/bazhenov/tango), a benchmarking framework. When comparing two algorithms, if one happens to run mostly on P-cores while the other gets pushed to E-cores, you're not comparing algorithms anymore – you're comparing hardware. I needed to check the proportion of time each process spends on P and E cores.

Getting there turned out to be a fun journey. In this article I'll walk through my findings. I also built a simple CLI tool that does it – [thread-counters](https://github.com/bazhenov/thread-counters).

## Obvious solution

The obvious starting point for research is the `taskinfo` tool, that on macOS reports the required info.

```console
# taskinfo $$
process: "zsh" [37483]
[...]
P-time:   0.334611 s (78.48%) (1173.36M cycles, 3.77G instructions, IPC 3.211, 3.51Ghz, 1152.03mJ, 3.44W (98.75%)) user/system: 0.181560 / 0.153051 (54% / 46%)
E-time:   0.091745 s (21.52%) (175.17M cycles, 183.27M instructions, IPC 1.046, 1909.25Mhz, 14.63mJ, 159.42mW (1.25%)) user/system: 0.036793 / 0.054952 (40% / 60%)
P/E switches: 122 (14%)
[...]
```

Here we can see that most of time was spent on P cores, but there was some spillover. Also 14% of context switches were performed with migration between different Performance Levels (P->E and vice versa).

It also has the `--threads --threadcounts=1` options that will provide the same information per thread.

`taskinfo` is an important diagnostic tool and is very useful on many occasions, but it doesn't fit my particular context for several reasons:

- it's hard to integrate `taskinfo` into benchmarking. I need to do about 400 measurements every second (10ms sampling rate, 2 measurements per sample, 2 processes). Executing an external process that requires milliseconds of time will add >10% overhead (my estimate – closer to 30-40%).
- besides the P/E ratio, it dumps a lot of additional info which is useful for general diagnostics but is not needed for my case.
- because of the previous point (I think), it requires sudo, which I'd prefer to avoid requiring from a user.

So `taskinfo` doesn't fit, which means I need to figure out how `taskinfo` gathers this information.

## How `taskinfo` gathers the P/E ratio?

After analyzing `taskinfo` binary, I found out that the target library call for getting all the info is – `proc_pidinfo(PROC_PIDTHREADCOUNTS)`. The good news is that almost all of the relevant info is actually [published by Apple](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/proc_info_private.h#L197-L227):

```c
// PROC_PIDTHREADCOUNTS returns a list of counters for the given thread,
// separated out by the "perf-level" it was running on (typically either
// "performance" or "efficiency").
//
// This interface works a bit differently from the other proc_info(3) flavors.
// It copies out a structure with a variable-length array at the end of it.
// The start of the `proc_threadcounts` structure contains a header indicating
// the length of the subsequent array of `proc_threadcounts_data` elements.
//
// To use this interface, first read the `hw.nperflevels` sysctl to find out how
// large to make the allocation that receives the counter data:
//
//     sizeof(proc_threadcounts) + nperflevels * sizeof(proc_threadcounts_data)
//
// Use the `hw.perflevel[0-9].name` sysctl to find out which perf-level maps to
// each entry in the array.
//
// The complete usage would be (omitting error reporting):
//
//     uint32_t len = 0;
//     int ret = sysctlbyname("hw.nperflevels", &len, &len_sz, NULL, 0);
//     size_t size = sizeof(struct proc_threadcounts) +
//             len * sizeof(struct proc_threadcounts_data);
//     struct proc_threadcounts *counts = malloc(size);
//     // Fill this in with a thread ID, like from `PROC_PIDLISTTHREADS`.
//     uint64_t tid = 0;
//     int size_copied = proc_info(getpid(), PROC_PIDTHREADCOUNTS, tid, counts,
//             size);

#define PROC_PIDTHREADCOUNTS 34
#define PROC_PIDTHREADCOUNTS_SIZE (sizeof(struct proc_threadcounts))
```

[`struct proc_threadcounts_data`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/proc_info_private.h#L89) contains instructions, cycles, system and user time spent in a given performance level.

```c
struct proc_threadcounts_data {
	uint64_t ptcd_instructions;
	uint64_t ptcd_cycles;
	uint64_t ptcd_user_time_mach;
	uint64_t ptcd_system_time_mach;
	uint64_t ptcd_energy_nj;
};
```

First you're supposed to determine how many performance levels there are on the given system using `sysctl`. Then you can use `proc_pidinfo(PROC_PIDTHREADCOUNTS)` to read thread counters separated by a performance level.

In the comment there is an explicit statement that the information is tracked by the OS on a per-thread level. The comment says: `Fill this in with a thread ID, like from PROC_PIDLISTTHREADS`.

And this is where I lost several days 🤦‍♂️, because this comment is actually wrong ☝️. You cannot use `PROC_PIDLISTTHREADS`, you have to use `PROC_PIDLISTTHREADIDS`. And yes, both will list thread identifiers for a given process.

## macOS has 2 different thread IDs?

...well, kind of. Technically both calls return integers that identify a thread in a unique manner. In order to understand, you need to look at the sources. Both actually activate a very similar code path inside `proc_pidinfo()`:

```c
	case PROC_PIDLISTTHREADIDS:
		thuniqueid = true;
		OS_FALLTHROUGH;
	case PROC_PIDLISTTHREADS:{
		error =  proc_pidlistthreads(p, thuniqueid, buffer, buffersize, retval);
	}
	break;
```

The only difference is the value of `thuniqueid` parameter which is used in `fill_taskthreadlist()`.

```c
int
fill_taskthreadlist(task_t task, void * buffer, int thcount, bool thuniqueid)
{
  [...]
  thaddr = (thuniqueid) ? thact->thread_id : thact->machine.cthread_self;
}
```

So:

- `PROC_PIDLISTTHREADIDS` – returns regular thread identifiers that we're used to
- `PROC_PIDLISTTHREADS` – returns `cthread_self`-pointers in kernel space to a `struct arm_saved_state64` which contains the CPU architecture state for a given thread.

The purpose of `cthread_self` pointers in this context remains unclear to me — if you know, I'd love to hear about it.

Anyway, this latter one is not what `PROC_PIDTHREADCOUNTS` expects. It expects regular thread IDs that can be listed using `PROC_PIDLISTTHREADIDS` or [`task_threads()`](https://developer.apple.com/documentation/kernel/1537751-task_threads). The advantage of `proc_pidinfo(PROC_PIDLISTTHREADIDS)` is that it does not require you to retrieve the task port for another application (eg. `task_for_pid()`) which requires a specific entitlement.

## Bringing it all together

Now we can build a simple CLI tool that lists P/E metrics for a given PID using the following procedure:

1. list number of performance levels and their names using `sysctl("hw.nperflevels")`/`sysctl("hw.perflevel{i}.name")`
2. list all thread IDs for a given PID using `proc_pidinfo(PROC_PIDLISTTHREADIDS)`
3. iterate over threads and read P/E metrics using `proc_pidinfo(PROC_PIDTHREADCOUNTS)` and thread names using `proc_pidinfo(PROC_PIDTHREADID64INFO)`

And here is the result:

```console
$ thread-counters `pgrep -x Safari`

        |                      PERFORMANCE                      |                      EFFICIENCY                       |
    TID |      usr      sys          cycles           insns IPC |      usr      sys          cycles           insns IPC |
  12801 |  1268.98   240.38   4326344607684   7641724509498 1.8 |   624.59   249.13   1555603231945   1082602205470 0.7 |
  12826 |    34.08    27.24    151211531442    167413362041 1.1 |    36.63    53.61    152207562562     82421607487 0.5 | com.apple.NSEventThread
  12850 |     0.00     0.00          104582           88941 0.9 |     0.00     0.00               0               0 0.0 | OGL Profiler
  12890 |     0.02     0.01        88718641       196686302 2.2 |     0.00     0.00         3914648         3863641 1.0 |
  13024 |    13.03     5.99     45761945364     60040662643 1.3 |     8.27     4.61     22711518200     14297786796 0.6 | WebCore: Scrolling
  13115 |    54.96     4.52    165496321282    111265239139 0.7 |    62.91     5.03    106277481783     24443002616 0.2 | Log work queue
  13210 |     0.00     0.00           53776           40788 0.8 |     0.00     0.00          555197          532557 1.0 | com.apple.CFSocket.private
  49214 |     0.00     0.00           22032           15948 0.7 |     0.00     0.00               0               0 0.0 | caulk.messenger.shared:17
  49215 |     0.00     0.00            7387           16106 2.2 |     0.00     0.00               0               0 0.0 | caulk.messenger.shared:high
1306370 |     0.00     0.01        21991125        18477708 0.8 |     0.00     0.00         6747916         2937571 0.4 | com.apple.CFNetwork.CustomProtocols
3419158 |     0.00     0.00         9025428         9270342 1.0 |     0.02     0.06       121609406       102582928 0.8 | ANEServicesThread
3419170 |     0.00     0.00         8546860         9347772 1.1 |     0.02     0.05       103717192       100299495 1.0 | ANEServicesThread
4828619 |     0.05     0.02       137245479       170221028 1.2 |     1.60     0.50      2672949220      1871335051 0.7 | JavaScriptCore libpas scavenger
4859210 |     0.00     0.00         9323881        11291823 1.2 |     0.01     0.02        48674657        23106448 0.5 |
4860249 |     0.00     0.00         1017455         1027368 1.0 |     0.01     0.01        30769073        13504687 0.4 |
4860250 |     0.00     0.00           46895           40902 0.9 |     0.00     0.00          224396           73600 0.3 |
4860252 |     0.00     0.00               0               0 0.0 |     0.00     0.00               0               0 0.0 |
4860253 |     0.00     0.00               0               0 0.0 |     0.00     0.00               0               0 0.0 |
4861766 |     0.00     0.00               0               0 0.0 |     0.00     0.00          755211          367622 0.5 | CVDisplayLink
```

## Conclusion

The OS tracks P/E usage time for each thread separately and you can read it using `proc_pidinfo(PROC_PIDTHREADCOUNTS)`. No sudo required, no special entitlements – just a straightforward `proc_pidinfo` call that works for any process running under the same user account.

The main gotcha is the misleading comment in the XNU sources that points you to `PROC_PIDLISTTHREADS` when you actually need `PROC_PIDLISTTHREADIDS`. These return subtly different kinds of "thread identifiers", and only the latter works with `PROC_PIDTHREADCOUNTS`. Hopefully this article saves someone a few days of debugging.

For my original use case in Tango.rs – verifying that benchmark workloads stay on P-cores – this works perfectly. I can now sample thread counters at high frequency with negligible overhead and get a clear picture of where each thread's cycles are actually spent.
