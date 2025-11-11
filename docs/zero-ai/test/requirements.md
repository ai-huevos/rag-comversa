# **Requirements Document: system0 (EARS-Compliant)**

Project: Operational Intelligence System (system0)  
Primary Interface: WhatsApp Multi-Modal (Text, Voice, Image, Document)  
Primary Language: Spanish (Latin American)

## **Glossary**

| Term | Definition |
| :---- | :---- |
| **system0** | The AI-powered Operational Intelligence System. |
| **PII** | Personally Identifiable Information (anonymized before LLM processing). |
| **RAG** | Retrieval-Augmented Generation. |
| **IntelligenceDB** | The core SQLite database storing extracted entities and metadata. |
| **Knowledge Graph** | The Neo4j database storing consolidated, cross-company entities and relationships. |
| **OCR** | Optical Character Recognition. |
| **STT** | Speech-to-Text. |
| **TTS** | Text-to-Speech. |

## **1\. The "I Send Data" Workflow (Ingestion & Quality Assurance)**

This workflow governs how the system captures, processes, and validates inputs from the user's WhatsApp channel.

### **R1. WhatsApp Channel Integration**

**WHEN** a user sends a message or document via WhatsApp, **THE System** **SHALL** accept the input via the WhatsApp Business API and route it to the Multi-Modal Processing pipeline.

### **R2. Multi-Modal Input Processing**

**WHEN** any input is received, **THE System** **SHALL** auto-detect the input type (text, audio, image, document, video) and generate a structured payload containing:

1. STT transcription and confidence (for audio/video).  
2. OCR text and confidence (for images/documents).  
3. Document type classification.

### **R2.1. Persistent User Identification**

**WHEN** a message is received via the WhatsApp API, **THE System** **SHALL** extract the sender's unique phone number and use it as the persistent UserID for all subsequent storage, context management, and audit trail logging.

### **R2.2. Spanish Language Support for STT/TTS**

**THE System** **SHALL** support Spanish (Latin American dialect) for:

* Speech-to-Text transcription.  
* Text-to-Speech voice synthesis.  
* Natural Language Understanding (intent, entity extraction).

**THE System** **SHALL** handle:

* Code-switching (Spanish \+ English in same message).  
* Regional accents and terminology (Mexican, Colombian, Bolivian, Argentine).  
* Business jargon specific to construction, hospitality, and QSR.

### **R3. STT Transcription and Correction Loop**

**IF** the STT confidence score is **\<80%**, **THE System** **SHALL** show the transcription to the user via WhatsApp and ask for confirmation or correction.

### **R4. OCR and Document Quality Feedback**

**IF** the OCR confidence score is **\<85%** on critical fields (e.g., financial amounts, dates, employee names), **THE System** **SHALL** send the user the highlighted source image/text snippet and allow correction via a follow-up voice note or text message.

### **R5. PII Anonymization Guardrail**

**BEFORE** data is sent to the LLM API, **THE System** **SHALL** detect, anonymize, and log all **PII** in the input payload according to the defined security policy.

### **R6. Specialized Document & Entity Extraction**

**WHEN** a document is classified (e.g., CONTRACT, ORG\_CHART), **THE System** **SHALL** use the specialized extraction pipeline to achieve **≥85%** accuracy for key entities (e.g., contract parties, org chart reporting lines, financial revenues).

### **R7. Full Audit Trail Maintenance**

**THE System** **SHALL** log every processing step for a given input with a timestamp, the confidence score for that step, and the prompt version used, preserving the original source media for a complete audit trail.

## **2\. The "System Learns" Workflow (Core Intelligence & Consolidation)**

This workflow defines the internal processing, validation, consolidation, and self-improvement of the knowledge base.

### **R8. Core Entity Extraction Accuracy**

**THE System** **SHALL** extract all 17 defined entity types from all processed Spanish inputs and achieve an entity extraction accuracy of at least **85 percent** for "pain point," "process," and "system" entities.

### **R9. Extracted Entity Validation**

**WHEN** entity extraction is complete, **THE System**'s ValidationAgent **SHALL** perform consistency checks to:

1. Check for entities with descriptions shorter than 5 words.  
2. Identify and flag plausible hallucinations.  
3. Check for internal logical inconsistencies (e.g., an invoice date before a purchase date).

### **R10. Cross-Company Knowledge Consolidation**

**THE System** **SHALL** use the **KnowledgeConsolidationAgent** to identify and propose duplicate entities using semantic similarity **across all three companies** (Comversa, BF, Los Tajibos) and store consolidated entities in the **Knowledge Graph**.

### **R11. Operational Workflow Automation**

**WHEN** the **Pain Point** entity is extracted, **THE System** **SHALL** automatically link it to a proposed **Process Improvement** entity or a **System Change Request** entity.

### **R12. User Correction Feedback Loop**

**WHEN** a user submits a correction via the feedback loop (R4 or R21), **THE System** **SHALL** record the correction as ground truth and flag the associated entity and prompt version for use in future model fine-tuning.

## **3\. The "I Ask Questions" Workflow (Query & Discovery)**

This workflow focuses on the user-facing natural language query interface and intelligent response generation.

### **R13. Conversation Context Management**

**WHEN** a follow-up query is received, **THE System** **SHALL** retrieve relevant context (previous messages, extracted entities, and inferred company/project) from the conversation history to resolve ambiguous follow-up queries.

### **R14. RAG-Grounded Query Response**

**WHEN** a user submits a natural language query via WhatsApp, **THE System** **SHALL** use the **RAG** pipeline to:

1. Retrieve relevant context from both the **IntelligenceDB** and the **Knowledge Graph**.  
2. Generate an answer grounded in the retrieved data.  
3. Cite the source documents or consolidated entities used to generate the answer.

### **R15. Intelligent Response Format Selection**

**THE System** **SHALL** select a response format (text, TTS voice note, visual chart/graph, or exported PDF/Excel file) based on the user's query intent, and deliver the response via WhatsApp.

### **R16. Voice Message Preferences**

**THE System** **SHALL** provide a persistent configuration setting for each user's UserID (R2.1) to override the intelligent format selection (R15) and force responses to **always** be delivered as a TTS voice note or **always** be delivered as text.

### **R17. Proactive Pattern Discovery**

**THE System** **SHALL** provide a natural language query mechanism to surface **Cross-Company Patterns** (e.g., "Which two companies share the highest-rated supplier?" or "What are the top 3 recurring pain points across the group?").

## **4\. System Reliability and Governance**

This workflow covers the core technical guardrails, security, and maintenance requirements necessary for a production-grade system.

### **R18. Real-Time Operational Alerting**

**WHEN** extracted data crosses a configurable threshold (e.g., 3+ high-severity pain points related to a single system in one week), **THE System** **SHALL** trigger an automated **Operational Alert** and deliver it as a WhatsApp notification to the designated manager.

### **R19. API Failure Handling & Fallback**

**IF** an API call fails with a transient error, **THE System** **SHALL** retry the call with exponential backoff for a maximum of 3 attempts, and then **SHALL** fallback to the next model in the defined 6-model fallback chain.

### **R20. API Cost Control Mechanism**

**THE System** **SHALL** enforce a hard limit of **1000.00 USD** per calendar month for all API costs and **SHALL** send an alert when the cumulative monthly cost reaches 900.00 USD.

### **R21. Performance and Caching**

**THE System** **SHALL** process a batch of 44 interviews in less than **20 minutes** by processing at least **4 inputs in parallel** and utilizing a caching layer for duplicate extraction calls.

### **R22. Prompt Versioning and A/B Testing**

**THE System** **SHALL** record the prompt version ID used for each entity extraction in the **IntelligenceDB** and **SHALL** provide a configuration setting to run A/B tests on two different prompt versions simultaneously.

### **R23. Evaluation Pipeline**

**THE System** **SHALL** maintain a test set of 30 labeled inputs with ground truth entities and **SHALL** provide a script to generate a report detailing entity extraction F1 score, accuracy, and fact completeness.

### **R24. Security and Access Control**

**THE System** **SHALL** use parameterized queries for all database operations and **SHALL** restrict database access to authorized service accounts only.

### **R25. Operations and Observability**

**THE System** **SHALL** provide a health check endpoint that reports the status of the database and API connectivity, and **THE System** **SHALL** track extraction progress by displaying the number of inputs processed, pending, and failed.