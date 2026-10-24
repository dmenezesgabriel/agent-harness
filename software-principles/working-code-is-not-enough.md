# Working code is not enough

## Tatical mindset

Focused on getting features working as quickly as possible.

This approach makes nearly impossible to produce a good system design. It make looks perfectly fine introducing small **kludge** if that allows the current task to be completly more quickly.

While complexity is incremental, we must avoid that adopting a [Zero tolerance philosophy](software-issues/symptons-of-complexity.md#Zero-tolerance-philosophy).

We must avoid **shortcuts**, is no acceptable to introduce unnecessary complexities in order to finish your current task faster. The most important thing is the long-therm structure of the system.

Most of the code in any system is written by extending codebase, so your most important job as a developer is to facilitate future extensions.

## Strategical approach

Invest time to produce clean designs and fix problems. Rather than thinking on the fastest path to finish your current project, you must improve the design of the system.

Your goal must be to produce a great design, which also happens to work.

Great design first, working code as a consequence.

Try a couple of alternative designs the pick the cleanest one. Try to imagine a few ways in which the system will might need to be changed in the future and make sure will be easy with your design.

When you discover a design problem, don't just ignore it or patch arround it, take a little extra time to fix it.

A huge up-front investiment, such as trying to design the entire system, won't be effective. The ideal design tends to emerge in bits and pieces, as you get experience with the system. Thus, the best approach is to make lots of small investiments on a **continual basis**.

Do not be a **tatical tornado**.

The therm _techinical debit_ is often used to describe the problems caused by tactical programming. By programming tatically you are borrowing time from the future: development will go more quickly now, but more slowly later on.

> A philosophy of software design, 2nd edition.