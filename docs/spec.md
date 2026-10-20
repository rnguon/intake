# Intake: Product Spec

Status: draft · Owner: John Doe · Last updated: October 2026
## Problem

Pacific Marketplace (a fictional online store) answers customer requests through one shared support inbox. Agents read every message, decide what it is about and how urgent it is, look up the policy, and type a reply. Most requests repeat the same 15 questions in the FAQ, so support staff spend their time on routine sorting while urgent cases (double charges, locked accounts, account takeovers) wait in the same queue as newsletter questions.

## Key Features

**Goal:** Every request is categorized, prioritized and given a draft reply grounded in the FAQ within 60 seconds by an AI agent, so support staff need to only review, edit and approve.

**Assumed Volume** About 300 requests a week, peaking at 600 on holiday weeks, handled by 3 part-time agents.

Intake will be multi-tenant: each organization sees only its own requests, users and FAQ. 
## Users and roles

| Role      | Who                              | Can do                                                                               |
| --------- | -------------------------------- | ------------------------------------------------------------------------------------ |
| Requester | A customer; no account in Intake | Submit a request by web form or email                                                |
| Agent     | Support staff                    | See their organization's queue, edit drafts, approve and send, reject with a reason  |
| Admin     | Support lead                     | Everything an Agent can, plus manage FAQ documents, users and the monthly LLM budget |

## User stories
User stories are written in "As a / I want / so that" format to describe value from the user perspective. Each user story is then followed by "Given / When / Then" format to describe its acceptance criteria.

**S1. Submit a request (Requester)**
As a customer, I want to send my question through a web form so that I don't need an account.
- Given the public form, when I submit a message of 1–1000 characters with an email address, then I see a confirmation with a reference number within 5 seconds.
- Given the same submission is sent twice with the same idempotency key, when the second arrives, then no duplicate request is created and the same reference number is returned.
- Given any empty field in the web form, when I submit, then I see a validation error and nothing is stored.

**S2. See a triaged queue (Agent)**
As an agent, I want the queue sorted by priority so that urgent cases are handled first.
- Given new requests, when triage completes, then each shows a category, a priority and a confidence score.
- Given urgent and low requests, when I open the queue, then urgent requests appear first, then by oldest.
- Given a request from another organization, when I open the queue, then it never appears.

**S3. Review and approve a draft (Agent)**
As an agent, I want to edit and approve an AI draft so that replies stay accurate and on-policy.
- Given a triaged request, when I open it, then I see the draft reply and the FAQ entries it cites (for example faq-06).
- Given I edit and approve the draft, when I click Approve, then the reply is marked sent and the action is recorded in the audit log with my name and time.
- Given a draft with no FAQ citation, when I open it, then it is flagged "needs review".

**S4. Uncertain or failed triage goes to a human (Agent)**
As an agent, I want requests the system can't handle confidently to come to me clearly marked, so that nothing is lost or answered wrongly.
- Given triage returns a confidence below 0.6, when it completes, then the request is marked "needs human" and shows no draft.
- Given the LLM returns output that doesn't match the expected format, when triage runs, then the request is marked "needs human" and the error is logged, never shown to the customer.
- Given the LLM provider is down, when requests arrive, then they are still accepted and stored, triage retries up to 5 times with increasing delays, and after the last attempt the request is marked "needs human".
- Given a request in a language other than English, when triage completes, then it has a category and priority, is marked "needs human", and shows the detected language.

**S5. Reject a draft with a reason (Agent)**
As an agent, I want to reject a bad draft and say why, so that the team can improve the prompts.
- Given a draft, when I click Reject, then I must choose a reason (wrong category, wrong priority, wrong facts, wrong tone, other) before the rejection is saved.
- Given a rejected draft, when I reject it, then I can write my own reply and approve that instead.
- Given rejected drafts exist, when an admin exports them, then each row includes the request, the draft, the reason and the agent's corrected labels, ready to add to the eval set.

**S6. Manage FAQ documents (Admin)**
As an admin, I want to load and update my organization's FAQ, so that drafts reflect current policy.
- Given a Markdown FAQ with sections named faq-01, faq-02 and so on, when I load it, then each section is stored and searchable within 2 minutes.
- Given an updated FAQ, when I load it again, then the old version is fully replaced in one step, and no draft created afterwards cites a removed section.
- Given two organizations with different FAQs, when a request is triaged, then only its own organization's FAQ is used.
- (Version 1 loads FAQs with a command-line tool; an upload screen is a stretch goal.)

**S7. Set a monthly LLM budget (Admin)**
As an admin, I want a spending cap on AI usage, so that costs can't run away.
- Given a monthly budget, when spending reaches 80%, then admins receive one email warning.
- Given spending reaches 100%, when new requests arrive, then they are still accepted and categorized as "needs human" without calling the LLM, and the queue shows a "budget reached" banner.
- Given a new month starts, when the first request arrives, then spending resets to $0 and triage uses the LLM again.

**S8. Manage users and roles (Admin)**
As an admin, I want to add and remove agents, so that only current staff can see customer requests.
- Given I invite a person by email as an Agent, when they accept, then they can see their organization's queue and nothing else.
- Given an Agent, when they open an admin page or call an admin API, then they get a 403 error.
- Given I remove a user, when they make their next request, then their session is no longer valid.
- Given I am the only admin, when I try to remove myself, then the action is blocked with an explanation.

**S9. Audit history (Admin)**
As an admin, I want a record of every action, so that I can answer "who changed this and when".
- Given any state change (triage, edit, approve, reject, role change, FAQ load), when it happens, then an audit entry records who, what, when, and the before and after values.
- Given the application's database account, when it tries to update or delete an audit entry, then the database refuses.
- Given a request ID or a user, when I filter the audit history, then I see their entries newest first.

**S10. Prompt-injection safety (all)**
As the support lead, I want customer text treated only as data, so that nobody can manipulate triage or replies by hiding instructions in a request.
- Given a request containing instructions such as "ignore previous instructions" or a hidden comment (req-0055, req-0056), when triaged, then its category and priority match the same request with the instructions removed.
- Given such a request, when a draft is created, then it does not promise refunds, credits or actions the FAQ doesn't support, and reveals no system prompt, FAQ list or other customers' data.
- Given a suspected injection, when an agent opens the request, then it is flagged "possible manipulation attempt".
- Given any request, when it is processed, then the LLM has no ability to send messages, change records or read another organization's data.

## Non-functional requirements

| ID | Requirement | Target | How measured |
| --- | --- | --- | --- |
| NFR-1 | Read latency | p95 under 300 ms at 50 requests/second | k6 load test (Lesson 11) |
| NFR-2 | Triage speed (SLO) | 99% of requests triaged within 60 s, over 30 days | Cloud Monitoring SLO (Lesson 10) |
| NFR-3 | Triage accuracy | Category accuracy at least 85% on the 65-row eval set | `make eval` (Lesson 7) |
| NFR-4 | Injection resistance | 0 of all `[injection]` cases change category, priority or draft | Eval report |
| NFR-5 | Tenant isolation | 0 rows from another tenant on any endpoint | Isolation test (Lesson 5) |
| NFR-6 | LLM cost | Under $0.002 per request; hard monthly cap per tenant | Cost metric per tenant |
| NFR-7 | Availability | Zero-downtime deploys; rollback under 1 minute | Rollback drill (Lesson 9) |
| NFR-8 | Privacy | Emails and phone numbers redacted before any LLM call; data deleted on request | Test plus provider request logs |

## Non-goals (version 1)

- No automatic sending: a person approves every reply.
- No attachment handling or image reading.
- No live chat; requests arrive by form or email only.
- No integration with the store's order system; agents look up order details themselves.
- No mobile app.
- No languages other than English for drafts; non-English requests are categorized and flagged for a human.

## Assumptions and open questions

- [ ] Volume and staffing numbers are assumptions for a fictional organization.
	- [ ] About 300 requests a week, peaking at 600 on holiday weeks, handled by 3 part-time agents.
- [ ] Should non-English requests get drafts in the customer's language? (Currently a non-goal.)
	- [ ] The original language and translated language can be shown for the customer request. The drafts and response should be in English. 
- [ ] How long are requests kept? 
	- [ ] 12 months, then deleted.
- [ ] Is "urgent" handled within a target time by agents? 
	- [ ] Within 2 business hours.
