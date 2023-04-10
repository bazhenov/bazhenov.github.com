---
date: 2023-03-28
title: Why Clean Code was (and still is) important?
url: posts/why-clean-code-was-important
layout: post
tags: performance
---

In recent years, criticism of the classic object-oriented analysis and design ideas has grown increasingly louder. One example of such criticism is [Clean Code, Horrible Performance][clean-code] by Case Muratori.

[clean-code]: https://www.computerenhance.com/p/clean-code-horrible-performance

Here's a quote that explains the author's idea:

> It simply cannot be the case that we're willing to give up a decade or more of hardware performance just to make programmers’ lives a little bit easier. Our job is to write programs that run well on the hardware that we are given. If these rules cause software to perform this poorly, they simply aren't acceptable.

Well, actually, it is the case. We relinquished a decade's worth of hardware advancements solely to facilitate the lives of programmers. And this is clearly accepted by the industry. But there are some very good reasons for it. Even if I mostly agree with the author, – it's a sad state of the affair.

In this post, I want to talk about what it means to "run well". The industry has yet to reach a consensus on the priority between computational efficiency and developer efficiency. Similar to the medical field, programming is not a homogenous profession, but rather a diverse one with various specializations, given the contemporary era's high degree of labor division. Consequently, being a software developer in the 21st century does not mean practicing a single occupation.

It's more productive to consider the context in which ideas flourish and take root. I suggest we think about the following question: **How did the methodologies that harm efficiency to such an extent become so widespread in the industry?**

## Why even bother?

If you're a firm believer in the idea that software should be developed with hardware in mind, then you should also build your career in a company that supports and encourages those kind of ideas and skills. Otherwise, you'll be swimming against the current. While we can challenge the reason for the direction of the status quo, and we can explore substitute approaches, it is contradictory to label the current way of developing software as erroneous.

The industry's evolution has not been a mere game of chance, nor solely due to the prevalence of silly ideas at a particular moment in the past. They persisted and survived, demonstrating that they are not without merit. Therefore, even if the principles of clean code are harmful (which I beleave are. Not only with respect to hardware, but with the respect to software developers too), we need to understand which of these harmful parts have been successful and why. Otherwise, in pursuit of performance, we will only make things worse.

## Coding Modalities

The reason for such opposition of ideas how the good code looks like, is absence of clear disctinction between several programming modalities or registers. Depending on the company you work in and what you work on, one modality or another will dominate.

### Time-to-Market-oriented systems

The majority of software developed in recent decades has been based on a simple premise.

_Most individuals do not highly value their time, hence performance is not a competitive feature in business._

Users will not pay double for a site or application that operates twice as fast. Software should be fast enough to avoid annoying the user, but nothing more.

Yes, Visual Studio's debugger [can't update the watch/register view quickly enough during step-by-step execution][vs]. In that sense, Visual Studio has become worse. But that's not the type of factor that drives product success in the vast majority of cases. That is regrettable, but undestandable.

[vs]: https://www.youtube.com/watch?v=GC-0tCy4P1U

However, it is a completely different scenario if you have twice as many users. This almost always leads to an increase in revenue.

Take a look at the almost any popular products: Google, Facebook, WhatsApp, Amazon. There was always an idea, and it's always not a performance. This is because performance alone is a weak concept for a business. There are much stronger ideas, such as unique content (Facebook), competitive pricing (Amazon), or an algorithm that locates useful information (Page Rank). These are the ideas that generate revenue.

The primary reason for such an orientation, I presume, is as follows: hardly any company succeeds on the first attempt. As Clayton Christensen wrote:

> 93% of successful companies had to change their initial strategy

which means that the first idea is almost certainly a failure. An orientation towards TTM necessitates flexibility, allowing for the replanning and changing of the vector of development.

Over the past 30 years, we have witnessed a phase of growth in our industry where it is much more critical to create a large quantity of similar software and optimize the technological aspects of its production. In this field, we have, in fact, achieved considerable success.

* we have been a significant increase in automation of software production processes (build tools);
* testing becoming a much more common practice in the industry;
* The quality of tool support for the programming process has also significantly improved (IDE, static code analysis, etc.);
* high-quality version control tools becoming widely used. Do you remember the days of SVN when branching was considered a luxury?

That's essentially it. We could conclude the post here. However, while the statement is true in the vast majority of cases, the interesting cases are precisely when it's not. So let's take look at some cases, when performance is matters.

### Resource-constrained systems

There are two basic categories of systems that are suitable for hardware-oriented programming ideas:

* Embedded software. Typically, there are limitations on RAM and peripheral constraints. You simply need to fit within these constraints, otherwise the system just won't work.
* Large internet systems with a significant number of servers. Size is important. In such systems, optimizations can significantly reduce hardware requirements, resulting in cost savings.

In both cases, company has a significant financial incentive to optimize the system for these resource constraints.

### Performance-oriented systems

Realtime systems are another example where hardware-centric approaches not only relevan, but is necessity

* control systems. If an autopilot fails to make a timely decision, its decision loses its significance because the environment has changed. You can't ask the world to wait while the autopilot calculates the necessary control signals to keep the plane flying in a straight line. The laws of physics don't wait. This phenomenon is also apparent in very simple situations, such as accelerating a brushless motor. The rotor exhibits inertia, and the motor windings must be energized when the stator and rotor are in the correct relative position.
* soft realtime systems, for example High-Frequency trading. HF-trading is an area where performance almost directly converts to profit. Stock market will not wait. At least it will not wait for you.
* game development. You can think of it as a form of a soft realtime, I guess. Performance is an obvious quality factor there. Low and unstable FPS destroys the enjoyable gaming experience.

It is perhaps not coincidental that people who advocate for performance orientation and oppose excessive abstractions are typically from the game development industry.

At least in part, I think, the success of the iPhone is due to the fact that idea was implemented efficiently enough not to harm the UX. Slick user interface and captivating animations would be not possible without consistent 60 fps rate.

## C and C++ are bad languages for creating performant software

And on top of all this, we have major methodological issues writing efficient software. This subject warrants its own article, but to sum it up: there is no clear, streamlined methodology for developing hardware-efficient code.

Modern comprehension of hardware-efficient code comes down to the following:

 * avoiding unnecessary indirect addressing and virtual calls;
 * predictable branching;
 * predictable memory access;
 * code recognizable enough by the compiler to be vectorized.

While we have strict and explicit control over the first aspect, control over the rest is often indirect or absent altogether.

In the 1980s, the C language was an ideal fit for the scalar processors of that time. Even naive code written in C was reasonably performant, simply because the language had two properties:

 * it was precise - that is, it did not contain abstractions that were unclear how to best translate into machine code;
 * it was complete - the language contained a complete set of abstractions and features that reflected all the functionality of the CPUs of that time. There were no complex microarchitectural aspects that were not reflected in the language, but which significantly affected the performance of the program.

There is simply no language for modern CPUs that meets these criteria. __Neither C nor C++ correspond to the nature of modern wide, superscalar processors with deep out-of-order execution, quite complex memory hierarchy and a significant portion of performance located in vector units__. Optimizing compilers try to save the day as much as possible. However, an optimizing compiler is not a programming paradigm. Of course, you can do intrinsics, but that's another level of headache which deserves another post.

## Conclusion

Over the last few decades, the software development industry has not been focused on optimizing performance because it doesn't necessarily lead to profitability. This may be disheartening for individuals who take pride in their profession, and I empathize with them. Personally, I share their sentiments.

The good news is that the factors driving this expansive industry growth are starting to run out. So it's quite possible that the next three decades will be very different from the previous ones.

However, if it's important to you to create software that's well-optimized for hardware, here are some tips that I consider essential:

* don't join startups in their early stages. The economic incentives within these projects may lead the development team in a direction that contradicts your goals. Exceptions apply to projects where you have a clear understanding that the business model of such a startup is unfeasible without intelligent hardware platform utilization;
* Look for a work in game development or in mature companies with significant hardware infrastructure, where there are economic incentives for hardware optimization. However, it is important to note that the entire company cannot be performance-oriented. Ensure that your role focuses primarily on this kind of work.
