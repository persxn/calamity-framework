---
id: cp.stl
title: The C++ standard library (STL)
track: cp
group: language
prereqs: [cp.cpp]
tags: [cp]
weaves_into: [cp]
aliases: [stl, standard template library, vector, set, map, priority queue]
band: 800
est_hours: 30
order: 20
summary: "Containers and algorithms that turn an idea into twenty lines: vector, sort, set, map, priority_queue, and their traps."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.stl`.

# Boss

Solve 6 problems rated 900 to 1200 that each hinge on choosing the right container, in 100 minutes, and state the cost of every container operation used.

Passes when:

- after `cf sync`, at least 5 of the 6 are accepted inside the sitting
- for each solution the learner names the container, why it fits, and the total complexity
- one solution is rewritten with a different container and the difference in cost is explained

# Weave

Later topics should be implemented with the STL first; hand-written structures come only when it cannot do the job.

# Topics

## vector | `vector`
level: 1
- `push_back`/`emplace_back`, `resize`, `assign`, `back`, 2D vectors
- cost model: appending is amortised O(1); inserting or erasing in the middle is O(n)

## sort-comparators | Sorting with comparators
needs: [vector]
level: 2
- `sort`, `stable_sort`, descending order with `greater<>()`, sorting by a key with a lambda
- a comparator must be a strict weak ordering: returning true for equal elements is undefined behaviour

## binary-search-functions | `lower_bound`, `upper_bound`, `equal_range`
needs: [sort-comparators]
level: 2
- first element `>= x` and first element `> x` in a sorted range; turn the iterator into an index
- count of elements in `[l, r]` as a difference of two bounds

## set-map | `set`, `map` and `multiset`
needs: [vector]
level: 2
- ordered containers with O(log n) insert, erase and find; iterate in sorted order
- use the member `s.lower_bound(x)`; `std::lower_bound` on a set is O(n)
- `multiset::erase(value)` removes every copy; erase one copy through `find`
- `map[key]` creates the key; use `find` or `count` to test membership

## unordered | `unordered_map` and `unordered_set`
needs: [set-map]
level: 3
- average O(1), worst case O(n) per operation; Codeforces tests target the default hash
- defend with a custom hash seeded from the clock, or use `map` when log n is affordable

## stack-queue-deque | `stack`, `queue` and `deque`
level: 1
- pick the container from the access pattern: last-in-first-out, first-in-first-out, both ends

## priority-queue | `priority_queue`
needs: [sort-comparators]
level: 2
- max-heap by default; min-heap with `priority_queue<T, vector<T>, greater<T>>`
- no decrease-key: push again and skip stale entries (lazy deletion)

## algorithms | Algorithm library essentials
needs: [vector]
level: 2
- `reverse`, `unique` with `erase`, `min_element`/`max_element`, `count`, `fill`, `iota`
- `accumulate` takes its type from the initial value: use `0LL`
- `next_permutation` over a sorted range; `nth_element`; `partial_sum`

## strings-stl | `string` tools
level: 1
- `substr` copies (O(length)); `find`, `to_string`, `stoll`; character arithmetic with `c - 'a'`
- building a string by repeated `s = s + c` is quadratic; use `+=`

## iterators | Iterators and invalidation
needs: [set-map]
level: 3
- `begin`/`end`, `rbegin`, `prev`/`next`, distance between iterators
- what invalidates an iterator: vector growth, erasing while iterating; the safe erase loop

## bitset | `bitset`
needs: [vector]
level: 3
band: 1600
- fixed-size bit arrays with `&`, `|`, `^`, shifts and `count()`
- the factor-64 speed-up it buys for knapsack-style and reachability loops

## pbds | Order-statistics tree (GNU policy-based structures)
needs: [set-map]
level: 4
band: 1600
- `find_by_order(k)` and `order_of_key(x)` on an indexed set
- GNU-only: available with g++ on Codeforces, not portable
