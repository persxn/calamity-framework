# Third-party notices

The engine uses the Python standard library only. One part of it is derived
from published work by others.

## FSRS (Free Spaced Repetition Scheduler)

`engine/cal/fsrs.py` is an independent port of the FSRS-6 scheduling
formulas and uses the FSRS-6 default parameters as shipped by py-fsrs 6.3.2.
`engine/tests/fixtures/fsrs_reference.json` holds review sequences computed
with py-fsrs 6.3.2, against which the port is tested.

- Project: https://github.com/open-spaced-repetition/py-fsrs
- Licence: MIT

```
MIT License

Copyright (c) 2022 Open Spaced Repetition

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Data sources the engine can read

- Codeforces, through its public API (https://codeforces.com/apiHelp), only
  when a learner runs the `cf` commands with their own handle.

Exam facts in `framework/gate/` and the topic lists of the GATE tracks were
compiled from the documents published by the organising institute; each
file names its source and the date it was read.
