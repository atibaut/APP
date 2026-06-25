# Raport

# TECHNICAL REPORT

## 1. Introduction to the Coding Environment

This section describes the tools used to build the calculator. The choices were not arbitrary — each one solved a specific problem I ran into, and understanding why I picked them is part of understanding how the project developed.

### 1.1 GitHub: Version Control and Project Sharing

GitHub handles version control and sharing of the project source code, including the associated IfcProject files. Every change is stored with a timestamp and a commit message, which means I always had a recoverable history of the codebase. When I introduced a bug — and there were several — I could roll back to the last working state instead of trying to manually undo changes line by line.

In structural engineering, document control is a formal requirement. Git history is effectively a software-level equivalent: it shows what changed, when, and why. That traceability matters if the tool ever needs to be audited or handed to someone else.

### 1.2 Visual Studio Code: More Than Just a Text Editor

I had used basic text editors before, but VS Code felt different from the first day. It handles Python interpreter management through the Command Palette cleanly, and works the same way across Windows, macOS, and Linux, so switching machines mid-project was never an issue.

The part I appreciated most, though, was how it helped with the mathematics. I did not have to manually hunt for every Eurocode formula or transcribe equations from PDF standards into code by hand. The development environment, combined with its AI assistant, helped me find and apply equations that were already structured around current Eurocode 2 conventions. That accelerated the build of the calculation core significantly — instead of spending time cross-referencing clause numbers, I could focus on whether the logic was structurally correct.

That said, the assistant had clear limits. It was good at scaffolding code and finding formulae, but it repeatedly misunderstood the structural reasoning behind specific implementation decisions. That tension is discussed in more detail in Section 4.4.

### 1.3 Why Python? The Case for Object-Oriented Programming

Python was the natural choice for a structural calculation tool because its OOP model maps well onto how engineers already think about cross-sections. A beam is an object. It has geometry, material properties, and methods that operate on those properties to produce design values. Writing it that way felt intuitive in a way that purely procedural code would not.

---

## 2. Main Idea and Everyday Engineering Application

### 2.1 Purpose and Scope of the Tool

The calculator automates two calculations that appear constantly in the design of rectangular reinforced concrete beams:

- Effective depth (d): the distance from the extreme compression fibre to the centroid of the tension reinforcement, accounting for cover, bar diameter, and row spacing;
- Required reinforcement area (As): the cross-sectional area of bottom tensile steel needed to resist the applied bending moment.

All calculations follow Eurocode 2 (EN 1992-1-1), with Concrete C30/37 and steel grade S500 as the baseline materials. These are standard mid-range specifications used across European practice, which made them the sensible defaults for a general-purpose tool.

### 2.2 Why I Built This

The honest reason is that last semester I spent a lot of time doing these calculations by hand. Every new beam meant going through the same sequence: compute the centroid, subtract from total depth, find k, check the 0.167 limit, compute z, divide the moment. The process itself is not complicated, but doing it twenty times for a single project becomes monotonous very quickly, and monotonous work invites transcription errors.

I wanted to build something that handles all of that routine work automatically, so that when I sit down to design a structure, I can direct my attention to the decisions that actually require engineering judgement: is this section geometry appropriate, does the reinforcement arrangement allow proper concrete consolidation, does the design still work if I change the load combination. The calculator does not replace that thinking. It just removes the part that was eating my time without adding anything intellectually.

---

## 3. Error Analysis and Future Improvements

The first working version of the code had no defensive programming at all. It assumed every input was valid, every intermediate result was positive, and every division had a non-zero denominator. That assumption broke quickly. Below is an honest account of what went wrong and why.

### 3.1 Division by Zero — Two Separate Failure Points

#### Failure in `calculate_effective_depth()`

The effective depth is computed as d = h − centroid. If the centroid calculation produces a value equal to or greater than the total section height h, the result is zero or negative. Any downstream formula that uses d then either divides by zero or produces a physically nonsensical negative reinforcement area.

A concrete example: with h = 250 mm, cover = 50 mm, bar diameter = 25 mm, two rows, and row spacing = 100 mm, the centroid lands at exactly 125 mm — half the section height. Increase the spacing slightly, or add a third row, and d goes negative. The programme had no awareness of this.

#### Failure in `calculate_reinforcement_area()`

Line 33 computes the moment capacity factor as k = M / (b × d² × fcd). If either b or d is zero — which can happen if the effective depth calculation already failed — this expression crashes immediately. A second division on line 40, As = M / (z × fyd), is equally vulnerable: if the lever arm z approaches zero, the calculated reinforcement area explodes toward infinity.

Both of these are cascading failures — one bad input at the top of the calculation chain propagates silently until something divides by zero and the programme terminates without a useful message.

### 3.2 The Width Formula — A Structural Logic Error

This one bothered me most because it was not a programming mistake — it was a structural thinking mistake. The original formula I used to check whether a given number of bars fit within the beam width was:

bars × dia + (bars−1) × spacing ≤ b

The problem is straightforward once you see it: the formula accounts for bar diameters and the spacing between them, but makes no allowance for the concrete cover on each side of the section. Cover is not optional — it is a Eurocode 2 requirement that provides both corrosion protection and fire resistance. Ignoring it means the programme could approve reinforcement arrangements that physically do not fit once the cover zone is respected.

The correct condition, which I should have written from the start, is:

2 × cover + bars × dia + (bars−1) × spacing ≤ b

There is a related issue in calculate_bars() at line 65, where available width is derived as b − 2 × cover. If the cover value exceeds b/2, available width goes negative — a physically impossible state that the programme silently accepted and continued computing with rather than stopping and flagging the input as invalid.

### 3.3 Missing Input Validation Across the Board

The main input block had no validation at all. A user could enter a negative section width, a zero bar diameter, a non-integer number of rows, or plain text where a number was expected. Each of those scenarios either crashes the programme or, worse, silently produces nonsensical results. The specific unguarded inputs were:

- d_rebar, b, h: no checks for zero or negative values
- n_rows: integer cast with no check for negative values or zero
- All float inputs: no try-except blocks, so entering alphabetic characters crashes the programme immediately

### 3.4 Planned Fixes

In order of priority:

1. Input validation function: A dedicated function that checks type, sign, and physical plausibility before any calculation starts
2. Bounds checking on d and z: Explicit guards before any division, with clear error messages explaining what failed and why
3. Corrected width formula: Replace all instances of the cover-omitting check with the complete 2×cover version

---

## 4. Biggest Challenges: Edge Cases and Structural Constraints

### 4.1 Solution Optimisation and Preferred Bar Arrangements

The programme does not simply return the minimum calculated steel area. It searches for arrangements that use one or at most two rows of bars — what I call "preferred solutions." The reason is practical: single-row arrangements are easier to position accurately during construction, simplify formwork setup, and reduce the risk of concrete consolidation problems that occur when bars are clustered too tightly and the concrete cannot flow around them. A technically valid two-row arrangement is not always a good construction arrangement, and the tool tries to reflect that.

### 4.2 Compression Reinforcement and the k > 0.167 Limit

When the normalised moment factor k exceeds 0.167, the concrete compression zone cannot carry the moment alone — a singly reinforced section is no longer adequate and compression reinforcement in the upper part of the beam becomes necessary. The current programme handles this by stopping at line 32 and returning none, with a warning to the user that the section needs to be redesigned before proceeding.

This is intentionally conservative. Doubly reinforced sections require additional Eurocode 2 checks and introduce design choices that go beyond what this tool currently handles. Letting the programme guess at a solution there would be more dangerous than stopping it.

### 4.3 Bar Spacing Constraints

Eurocode 2 requires that the clear spacing between adjacent bars satisfies a minimum of max(20 mm, bar diameter). The calculator enforces this, but implementing it was more awkward than expected - the minimum spacing depends on the bar diameter, which is itself one of the variables the tool is trying to optimise. The result is a constraint that is inherently coupled to the solution it is constraining.

### 4.4 Working with an AI Assistant 

The integrated AI assistant in VS Code was genuinely helpful for the early stages. It could scaffold boilerplate quickly, suggest Eurocode-aligned formulae, and catch obvious syntax issues. I found myself relying on it less as the logic became more structurally specific, because that is where it started to struggle.

The structural reasoning was the main sticking point. When I tried to explain why the bar-fitting check needed to account for cover, or why a negative effective depth should terminate the calculation rather than produce a warning and continue, the assistant would acknowledge the correction and then reproduce the same mistake in the next iteration. It was writing syntactically correct Python that was structurally wrong — and structurally wrong code in this context does not just produce bad output, it produces output that looks plausible but is unsafe.

The more frustrating problem was cross-section visualisation. I wanted the programme to generate a clear diagram of the beam cross-section: the correct number of bars at their actual diameters, spaced as specified, within the section boundary, with the cover zone visible.

The AI consistently misinterpreted the spatial requirements. It would place bars at wrong positions, ignore the spacing constraints I had just explained, render the cover zone incorrectly, or produce a diagram that looked roughly right for the example case but broke immediately when the bar count or diameter changed. I spent a disproportionate amount of time on this — explaining the same geometric layout rules repeatedly, only to get back a drawing that violated them in a new way. Eventually I deprioritised the visualisation feature and focused on getting the calculation logic solid first. 

The overall lesson from both of these issues is the same: AI tools are accelerators, not engineers. The formula-finding was useful. The structural decision-making had to stay entirely with me.

---

## 5. Conclusion

Building this tool taught me more about defensive programming and structural logic than I expected. The Eurocode 2 calculations are not complex — but making them reliable, handling the cases where inputs are wrong or intermediate results go negative, and presenting the output in a way that reflects real construction constraints, all of that took considerably more work than the core arithmetic.

The bugs documented in Section 3 were each instructive. The division-by-zero failures were straightforward programming oversights. The cover omission in the width formula was a structural thinking error dressed up as a code error — which is arguably worse, because it would have produced results that looked reasonable while being non-compliant with Eurocode durability requirements.

The AI assistant accelerated the early work and slowed down the later work. That ratio feels right for a domain-specific engineering tool: generic coding tasks benefit from AI assistance, while domain-specific structural decisions do not. The visualisation challenge was the clearest demonstration of that boundary.