# Methodology alignment TODO

Status: proposed approach, pending implementation and code review.

Goal: on screens wider than 900px, the introduction's first line begins beside the heading's last line. At 900px and below, retain the stacked layout.

- [ ] Keep `.method-head` as a two-column desktop grid with explicit column proportions.
- [ ] Set `align-items: start` and remove the introduction's margin.
- [ ] Measure the heading's bottom relative to the top of `.method-head`, then subtract the heading's computed line-height to find where its last line begins.
- [ ] Apply that distance as `.method-introduction` top padding. Keep it in normal layout flow so the methodology steps move down without overlapping the introduction.
- [ ] Recalculate when available width or heading wrapping changes, using a `ResizeObserver`, and after fonts finish loading. Confirm how the measurement script can execute in the existing Streamlit rendering setup before implementation.
- [ ] In the media rule for widths of 900px and below, use one column and reset the introduction's top padding.
- [ ] Check several desktop widths, the 900px breakpoint, narrow screens, and sidebar states. Confirm wrapping, spacing, and absence of overlap with the steps.
- [ ] If exact text-baseline alignment is needed, adjust for the differing heading and paragraph font sizes. The measurement above aligns line boxes, not necessarily text baselines.
