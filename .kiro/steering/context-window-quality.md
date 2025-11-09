---
inclusion: always
---

# Context Window Quality Management

## Purpose
Monitor context window usage to maintain high-quality deliverables and alert the user when a fresh session might be beneficial.

## Context Window Thresholds

### Token Usage Monitoring
- **Green Zone** (0-100k tokens): Optimal performance, full context available
- **Yellow Zone** (100k-150k tokens): Monitor closely, quality still good
- **Orange Zone** (150k-175k tokens): Quality may start degrading, consider session refresh
- **Red Zone** (175k+ tokens): High risk of quality degradation, strongly recommend new session

## Alert Triggers

### When to Alert User

Alert the user when ANY of these conditions are met:

1. **Token threshold reached**: Context usage exceeds 150k tokens (75% of 200k budget)
2. **Complex task ahead**: About to start a multi-step implementation or refactoring
3. **Quality indicators**: 
   - Responses becoming verbose or repetitive
   - Missing important context from earlier in conversation
   - Need to re-read files already discussed
   - Difficulty tracking state across multiple files
4. **Long conversation**: Session has been running for 20+ exchanges
5. **Critical work**: About to work on production code, security features, or database migrations

### Alert Format

When threshold is reached, include this notice:

```
⚠️ CONTEXT WINDOW ALERT

Current token usage: [X]k / 200k ([Y]%)
Status: [Green/Yellow/Orange/Red] Zone

Quality Impact:
- [Describe any observed quality degradation]
- [Note what context might be getting compressed]

Recommendation:
[Continue/Consider new session/Strongly recommend new session]

Would you like to:
1. Continue in this session (I'll do my best to maintain quality)
2. Start a fresh session (I can provide a handoff summary)
3. Complete just this task, then start fresh

Your choice?
```

## Quality Preservation Strategies

### When Continuing in High-Token Sessions

If user chooses to continue despite warnings:

1. **Prioritize critical context**: Focus on essential files and information
2. **Minimize verbosity**: Be more concise in responses
3. **Avoid redundancy**: Don't repeat information already established
4. **Strategic file reading**: Only read files when absolutely necessary
5. **Checkpoint progress**: Suggest creating summary documents for complex work

### Session Handoff Protocol

When starting a new session, provide:

1. **Current state summary**: What was accomplished
2. **Active work**: What's in progress
3. **Next steps**: What needs to be done
4. **Key context**: Critical files, decisions, or constraints
5. **Handoff document**: Create `docs/SESSION_HANDOFF_[TIMESTAMP].md` if needed

## Monitoring Guidelines

### Self-Check Questions

Before starting major work, ask yourself:

- Am I in the Orange or Red zone?
- Is this task complex enough that quality matters significantly?
- Have I noticed any degradation in my responses?
- Would the user benefit from a fresh start?

### Proactive Alerts

Don't wait for user to notice quality issues. Alert proactively when:

- About to start a new major feature
- Switching to a different area of the codebase
- Beginning production-critical work
- Token usage crosses into Orange zone

## Examples

### Good Alert Timing

```
✅ "Before we start implementing the consolidation pipeline, I should mention 
   we're at 155k tokens (77%). This is a complex task - would you prefer to 
   start fresh so I have full context available?"
```

### Poor Alert Timing

```
❌ Waiting until 195k tokens and user notices quality issues
❌ Not alerting before critical database migration work
❌ Continuing to produce verbose responses in Red zone
```

## User Preferences

Track and respect user preferences:

- Some users prefer longer sessions (more continuity)
- Some users prefer fresh starts (maximum quality)
- Adapt alert frequency based on user feedback
- If user says "don't worry about it", reduce alert frequency but still warn for critical work

## Quality Indicators to Monitor

Watch for these signs of context degradation:

1. **Repetition**: Saying the same things multiple times
2. **Context loss**: Forgetting decisions made earlier
3. **Verbosity**: Responses getting unnecessarily long
4. **Confusion**: Needing to re-read files already discussed
5. **Inconsistency**: Contradicting earlier statements
6. **Reduced precision**: Less specific or accurate responses

## Summary

- Monitor token usage continuously
- Alert at 150k tokens (75% threshold)
- Always alert before critical/complex work in Orange/Red zones
- Respect user choice but provide clear recommendations
- Maintain quality through strategic context management
- Provide clean handoffs when starting new sessions

**Remember**: It's better to alert early and let the user decide than to deliver degraded quality work!
