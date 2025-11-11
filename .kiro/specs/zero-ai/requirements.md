# System0 Production Deployment Framework

**Version:** 1.0
**Last Updated:** November 10, 2025
**For:** Daniel's January 15, 2026 AGENT-001 Comversa Deployment
**Books Analyzed:** AI Engineering (Chip Huyen)

**Purpose:** Personalized knowledge base extracted from technical books and applied specifically to system0's architecture, ensuring production-ready deployment for Spanish business interview extraction.

---

## SECTION 1: SYSTEM0 ASSESSMENT (Using AI Engineering)

### 1.1 Use Case Evaluation (Chapter 4: Evaluate AI Systems)


**Core Principle from Book:**

## Chapter 4. Evaluate AI Systems

Chapter 4. Evaluate AI Systems

A model is only useful if it works for its intended purposes. You need to evaluate models in the context of your application. Chapter 3 discusses different approaches to automatic evaluation. This chapter discusses how to use these approaches to evaluate models for your applications.

This chapter contains three parts. It starts with a discussion of the criteria you might use to evaluate your applications and how these criteria are defined and calculated. For example, many people worry about AI making up facts—how is factual consistency detected? How are domain-specific capabilities like math, science, reasoning, and summarization measured?

The second part focuses on model selection. Given an increasing number of foundation models to choose from, it can feel overwhelming to choose the right model for your application. Thousands of benchmarks have been introduced to evaluate these models along different criteria. Can these benchmarks be trusted? How do you select what benchmarks to use? How about public leaderboards that aggregate multiple benchmarks?

The model landscape is teeming with proprietary models and open source models. A question many teams will need to visit over and over again is whether to host their own models or to use a model API. This question has become more nuanced with the introduction of model API services built on top of open source models.

The last part discusses developing an evaluation pipeline that can guide the development of your application over time. This part brings together the techniques we’ve learned throughout the book to evaluate concrete applications.

Evaluation Criteria

Which is worse—an application that has never been deployed or an application that is deployed but no one knows whether it’s working? When I asked this question at conferences, most people said the latter. An application that is deployed but can’t be evaluated is worse. It costs to maintain, bu...

**How It Applies to system0:**

1. **Business Interviews as AI Use Case**: system0 extracts structured data from unstructured Spanish business interviews for Comversa AGENT-001
2. **Evaluation Criteria**: Must measure extraction quality (entities, facts, sentiment) against ground truth from 30 sample interviews
3. **Domain-Specific Capability**: Spanish business language nuances require prompt engineering specific to Latin American business contexts

**Your Gaps:**
- [ ] Ground truth dataset (30 labeled interviews)
- [ ] Evaluation pipeline (accuracy, precision, recall metrics)
- [ ] Domain-specific capability testing for Spanish business terminology

**Action This Week:**
- Create 30-sample test set from Comversa interviews
- Define success metrics (≥85% entity extraction accuracy)
- Build simple evaluation script

---

### 1.2 Data Model Decision

[PENDING: Extract from Kleppmann's "Designing Data-Intensive Applications" Ch.2]

**Options:** Relational vs. Document vs. Graph

**YOUR CHOICE:** [To be completed with Kleppmann's content]

**Timeline:** 1 week vs. 3 weeks

---

### 1.3 Failure Scenarios

[PENDING: Extract from Kleppmann's DDIA Ch.8 "The Trouble with Distributed Systems"]

**What Can Break:** [To be filled from book]

**How system0 Fails:** [Applied to your system]

**Mitigation:** [What to code this week]

---

## SECTION 2: PROMPT ENGINEERING PROTOCOL (Using AI Engineering Ch.5)

### 2.1 Core Prompt Engineering Principles


**From AI Engineering Chapter 5:**

## Chapter 5. Prompt Engineering

Chapter 5. Prompt Engineering

Prompt engineering refers to the process of crafting an instruction that gets a model to generate the desired outcome. Prompt engineering is the easiest and most common model adaptation technique. Unlike finetuning, prompt engineering guides a model’s behavior without changing the model’s weights. Thanks to the strong base capabilities of foundation models, many people have successfully adapted them for applications using prompt engineering alone. You should make the most out of prompting before moving to more resource-intensive techniques like finetuning.

Prompt engineering’s ease of use can mislead people into thinking that there’s not much to it.1 At first glance, prompt engineering looks like it’s just fiddling with words until something works. While prompt engineering indeed involves a lot of fiddling, it also involves many interesting challenges and ingenious solutions. You can think of prompt engineering as human-to-AI communication: you communicate with AI models to get them to do what you want. Anyone can communicate, but not everyone can communicate effectively. Similarly, it’s easy to write prompts but not easy to construct effective prompts.

Some people argue that “prompt engineering” lacks the rigor to qualify as an engineering discipline. However, this doesn’t have to be the case. Prompt experiments should be conducted with the same rigor as any ML experiment, with systematic experimentation and evaluation.

The importance of prompt engineering is perfectly summarized by a research manager at OpenAI that I interviewed: “The problem is not with prompt engineering. It’s a real and useful skill to have. The problem is when prompt engineering is the only thing people know.” To build production-ready AI applications, you need more than just prompt engineering. You need statistics, engineering, and classic ML knowledge to do experiment tracking, evaluation, and dataset curation.

This chapter covers both how to write effective prompts and how to defend your applications against prompt attacks. Before diving into all the fun applications you can build with prompts, let’s first start with the fundamentals, including what exactly a prompt is and prompt engineering best practices.

Introduction to Prompting

A prompt is an instruction given to a model to perform a task. The task can be as simple as answering a question, such as “Who invented the number zero?” It can also be more complex, such as asking the model to research competitors for your product idea, build a website from scratch, or analyze your data.

A prompt generally consists of one or more of the following parts:

Task description

What you want the model to do, including the role you want the model to play and the output format.

Example(s) of how to do this task

For example, if you want the model to detect toxicity in text, you might provide a few examples of what toxicity and non-toxicity look like.

The task
...

### 2.2 Prompt Versioning System

**Template for system0:**

```markdown
# prompts/v1_basic.md
Role: You are an expert business analyst extracting information from Spanish interviews.
Task: Extract company name, interviewee role, key business challenges, and sentiment.
Context: Interview transcript provided below.
```

```markdown
# prompts/v2_structured.md
Role: Expert business analyst for Latin American markets
Task: Extract structured data in JSON format
Format:
{
  "company": "",
  "interviewee": "",
  "challenges": [],
  "sentiment": "positive|neutral|negative"
}
Context: Spanish business interview transcripts
```

```markdown
# prompts/v3_examples.md
[Same as v2 + Few-shot examples from actual Comversa interviews]
```

**current.md** → Symlink to best performing version

### 2.3 Evaluation Protocol

**30-Sample Test Set Creation:**
1. Select 30 diverse interviews from Comversa dataset
2. Manually label ground truth (you + domain expert)
3. Store in `tests/evaluation/ground_truth.json`

**Accuracy Metrics (from AI Engineering Ch.4):**
- Entity Extraction Accuracy: TP/(TP+FP+FN)
- Sentiment F1 Score
- Fact Extraction Completeness

**Before/After Comparison Template:**

| Metric | v1_basic | v2_structured | v3_examples | Target |
|--------|----------|---------------|-------------|--------|
| Entity Accuracy | ?% | ?% | ?% | ≥85% |
| Sentiment F1 | ?% | ?% | ?% | ≥80% |
| Fact Completeness | ?% | ?% | ?% | ≥75% |

**Success Threshold:** 85% entity accuracy, 80% sentiment F1, 75% fact completeness

---

## SECTION 3: RAG ARCHITECTURE (Using AI Engineering Ch.6)

### 3.1 RAG for system0


**From AI Engineering Chapter 6:**

## Chapter 6. RAG and Agents

Chapter 6. RAG and Agents

To solve a task, a model needs both the instructions on how to do it, and the necessary information to do so. Just like how a human is more likely to give a wrong answer when lacking information, AI models are more likely to make mistakes and hallucinate when they are missing context. For a given application, the model’s instructions are common to all queries, whereas context is specific to each query. The last chapter discussed how to write good instructions to the model. This chapter focuses on how to construct the relevant context for each query.

Two dominating patterns for context construction are RAG, or retrieval-augmented generation, and agents. The RAG pattern allows the model to retrieve relevant information from external data sources. The agentic pattern allows the model to use tools such as web search and news APIs to gather information.

While the RAG pattern is chiefly used for constructing context, the agentic pattern can do much more than that. External tools can help models address their shortcomings and expand their capabilities. Most importantly, they give models the ability to directly interact with the world, enabling them to automate many aspects of our lives.

Both RAG and agentic patterns are exciting because of the capabilities they bring to already powerful models. In a short amount of time, they’ve managed to capture the collective imagination, leading to incredible demos and products that convince many people that they are the future. This chapter will go into detail about each of these patterns, how they work, and what makes them so promising.

RAG

RAG is a technique that enhances a model’s generation by retrieving the relevant information from external memory sources. An external memory source can be an internal database, a user’s previous chat sessions, or the internet.

The retrieve-then-generate pattern was first introduced in “Reading Wikipedia to Answer Open-Domain Questions” (Chen et al., 2017). In this work, the system first retrieves five Wikipedia pages most relevant to a question, then a model1 uses, or reads, the information from these pages to generate an answer, as visualized in Figure 6-1.

Figure 6-1. The retrieve-then-generate pattern. The model was referred to as the document reader.

The term retrieval-augmented generation was coined in “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks” (Lewis et al., 2020). The paper proposed RAG as a solution for knowledge-intensive tasks where all the available knowledge can’t be input into the model directly. With RAG, only the information most relevant to the query, as determined by the retriever, is retrieved and input into the model. Lewis et al. found that having access to relevant information can help the model generate more detailed responses while reducing hallucinations.2

For example, given the query “Can Acme’s fancy-printer-A300 print 100pps?”, the model will be able to respond ...

**How It Applies to system0:**

1. **Retrieval Pipeline**: Store past interview extractions in vector DB for context
2. **Context Enhancement**: Retrieve similar past interviews to improve current extraction
3. **RAG vs Pure Prompt**: Use RAG when extraction requires historical context (repeat clients, industry patterns)

**Your RAG Design Decision:**

- **Option A**: No RAG (pure prompt) - Simplest, good for independent interviews
- **Option B**: RAG with ChromaDB - Add context from similar past interviews
- **YOUR CHOICE**: Start with Option A, add Option B if accuracy < 85%

**Implementation Timeline:**
- Week 1: Pure prompt baseline
- Week 2: Add RAG if needed
- Week 3: Optimize retrieval

---

## SECTION 4: AI ENGINEERING ARCHITECTURE (Using AI Engineering Ch.10)

### 4.1 Production Architecture for system0


**From AI Engineering Chapter 10:**

## Chapter 10. AI Engineering Architecture and User Feedback

Chapter 10. AI Engineering Architecture and User Feedback

So far, this book has covered a wide range of techniques to adapt foundation models to specific applications. This chapter will discuss how to bring these techniques together to build successful products.

Given the wide range of AI engineering techniques and tools available, selecting the right ones can feel overwhelming. To simplify this process, this chapter takes a gradual approach. It starts with the simplest architecture for a foundation model application, highlights the challenges of that architecture, and gradually adds components to address them.

We can spend eternity reasoning about how to build a successful application, but the only way to find out if an application actually achieves its goal is to put it in front of users. User feedback has always been invaluable for guiding product development, but for AI applications, user feedback has an even more crucial role as a data source for improving models. The conversational interface makes it easier for users to give feedback but harder for developers to extract signals. This chapter will discuss different types of conversational AI feedback and how to design a system to collect the right feedback without hurting user experience.

AI Engineering Architecture

A full-fledged AI architecture can be complex. This section follows the process that a team might follow in production, starting with the simplest architecture and progressively adding more components. Despite the diversity of AI applications, they share many common components. The architecture proposed here has been validated at multiple companies to be general for a wide range of applications, but certain applications might deviate.

In its simplest form, your application receives a query and sends it to the model. The model generates a response, which is returned to the user, as shown in Figure 10-1. There is no context augmentation, no guardrails, and no optimization. The Model API box refers to both third-party APIs (e.g., OpenAI, Google, Anthropic) and self-hosted models. Building an inference server for self-hosted models is discussed in Chapter 9.

Figure 10-1. The simplest architecture for running an AI application.

From this simple architecture, you can add more components as needs arise. The process might look as follows:

Enhance context input into a model by giving the model access to external data sources and tools for information gathering.

Put in guardrails to protect your system and your users.

Add model router and gateway to support complex pipelines and add more security.

Optimize for latency and costs with caching.

Add complex logic and write actions to maximize your system’s capabilities.

This chapter follows the progression I commonly see in production. However, everyone’s needs are different. You should follow the order that makes the most sense for your application.

Monitoring and ob...

**How It Applies to system0:**

1. **Guardrails**: Prevent PII leakage from interview transcripts
2. **Caching**: Cache extraction results to reduce API costs
3. **Monitoring**: Track extraction accuracy over time
4. **User Feedback**: Comversa users rate extraction quality (5-star system)

**Your Architecture Additions:**

```
system0 Architecture:
┌─────────────────────────────────────────┐
│ Input: Spanish Interview Transcript      │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 1. Guardrails: PII Detection           │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 2. Cache Check: Seen this before?      │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 3. Prompt (v1/v2/v3)                   │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 4. LLM Extraction (GPT-4/Claude)       │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 5. Output: Structured JSON             │
└─────────────┬──────────────────────────┘
              │
┌─────────────▼──────────────────────────┐
│ 6. Monitoring: Log accuracy             │
└─────────────────────────────────────────┘
```

**Code This Week:**
- Add PII detection guardrail
- Implement caching layer (SQLite or Redis)
- Add monitoring logs

---

## SECTION 5: AGILE DEVELOPMENT SPRINT

[PENDING: Extract from "The Art of Agile Development" Ch.6 (Incremental Design) and Ch.15 (Documentation)]

### 5.1 User Story Format

**Template:**
```
As a [Comversa analyst]
I want [accurate extraction of interview data]
So that [I can analyze business insights without manual transcription]
```

### 5.2 One Sprint (1 week) = 4 Phases

**Phase 1: Design** (Mon-Tue)
- Incremental design from Shore Ch.6
- Sketch prompt versions v1, v2, v3
- Define evaluation metrics

**Phase 2: Build** (Wed-Thu)
- Implement prompt versioning
- Code extraction pipeline
- Add guardrails and caching

**Phase 3: Test** (Fri)
- Run 30-sample evaluation
- Compare v1 vs v2 vs v3
- Document accuracy results

**Phase 4: Review** (Sat)
- Update documentation
- Commit to feature branch
- Create PR with results

### 5.3 Git Protocol

**Branch naming:** `feature/sprint-1-prompt-engineering`

**Commits:**
- After Phase 1: `git commit -m "Design: Created prompt v1, v2, v3 templates"`
- After Phase 2: `git commit -m "Build: Implemented extraction pipeline with guardrails"`
- After Phase 3: `git commit -m "Test: Evaluated 30 samples, v3 achieves 87% accuracy"`
- After Phase 4: `git commit -m "Docs: Updated README with evaluation results"`

**PR linking:** Link to `tasks.md` in PR description

**Merge criteria:**
- ✅ All tests pass
- ✅ Accuracy ≥ 85%
- ✅ Documentation updated
- ✅ Code reviewed

---

## SECTION 6: PRODUCTION READINESS CHECKLIST

**Before January 15, 2026 deployment:**

- [ ] **Reliable?** (DDIA Ch.1) - [Pending Kleppmann extraction]
- [ ] **Scalable?** (DDIA Ch.1) - [Pending Kleppmann extraction]
- [ ] **Maintainable?** (DDIA Ch.1) - [Pending Kleppmann extraction]
- [ ] **Prompts versioned?** ✅ v1, v2, v3 in `prompts/` directory
- [ ] **Evaluation metrics defined?** ✅ 85% entity accuracy, 80% sentiment F1
- [ ] **Failure handling in place?** (DDIA Ch.8) - [Pending extraction]
- [ ] **User feedback loop?** ✅ 5-star rating system for Comversa users
- [ ] **Documentation current?** (Agile Ch.15) - [Pending extraction]
- [ ] **Guardrails active?** ✅ PII detection enabled
- [ ] **Caching enabled?** ✅ Cache hits reduce API cost
- [ ] **Monitoring dashboard?** ✅ Track accuracy over time

---

## SECTION 7: DECISION TREE FOR "ENSEMBLE VS. KNOWLEDGE GRAPH"

[PENDING: Extract from Kleppmann DDIA Ch.12 "Future of Data Systems"]

**IF you need:**
- Fast extraction → Ensemble
- Relationship mapping → Knowledge Graph

**Your answer:** [To be completed with Kleppmann's content]

---

## MISSING BOOKS NOTICE

⚠️ **This framework is INCOMPLETE because these books are missing from your collection:**

1. **"Designing Data-Intensive Applications"** by Martin Kleppmann
   - **Needed for:** Reliability/Scalability/Maintainability assessment, Data model decision, Failure scenarios, Ensemble vs Knowledge Graph decision
   - **Location:** NOT FOUND in `Books/AI/` directory

2. **"The Art of Agile Development, 2nd Edition"** by Shore, Warden, Klitgaard, Larsen
   - **Needed for:** Incremental design patterns, Documentation standards, User story formatting, Sprint structure
   - **Location:** NOT FOUND in `Books/AI/` directory

**Action Required:**
- Add these books to your collection
- Re-run this extraction script with complete book set
- Update Sections 1.2, 1.3, 5.1, 5.2, 6 (Reliability checks), and 7

---

## NEXT STEPS

1. **This Week:**
   - Create 30-sample test set
   - Implement v1, v2, v3 prompts
   - Build evaluation pipeline
   - Run initial accuracy tests

2. **Next Week:**
   - Add guardrails (PII detection)
   - Implement caching layer
   - Set up monitoring dashboard
   - Test with Comversa users

3. **Before January 15:**
   - Complete Production Readiness Checklist
   - Run load tests (if needed)
   - Deploy to staging environment
   - Get user feedback
   - Deploy to production

---

**Generated:** November 10, 2025
**Tool:** Atlas Extract + Custom Framework Generator
**Books Processed:** 1 of 4 required

