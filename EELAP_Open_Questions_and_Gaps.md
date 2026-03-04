# EELAP -- Open Questions & Architectural Gaps Document

This document captures unresolved design decisions and edge cases to
ensure architectural completeness before development scaling.

------------------------------------------------------------------------

## 1. Role & Access Control

-   How are lecturer accounts created? --> They are seeded in (custom solution)
-   Is there an admin role? --> No, only lecturers and students
-   Can multiple lecturers share one lab series? --> There is one lecturer entity for a given lab.
-   What permissions are editable after roster lock? 

------------------------------------------------------------------------

## 2. Session Lifecycle Edge Cases

-   What happens if lecturer forgets to commit after auto-close?
-   Can sessions be reopened?
-   How are duplicate check-ins handled? --> See it as two layers when the reponse passes the layer of rotating code issue, ie its succesfully submitted, it is now typed as recieved, no matter what its state is (clean, flagged). So another response from the same account will not be allowed and we shall tell them your record has already been submited. 
-   What if code rotates mid-submission? --> wait and enter new valid one

------------------------------------------------------------------------

## 3. Geo-Location Reliability

-   What is the exact distance threshold? 
-   How do we handle GPS inaccuracy indoors?
-   Should device accuracy radius be stored?
-   Should IP-based heuristics be added?

------------------------------------------------------------------------

## 4. Anti-Fraud Extensions (Future)

-   Device fingerprinting?
-   Multiple accounts from same device detection?
-   Pattern-based anomaly detection?

------------------------------------------------------------------------

## 5. Data Integrity & Versioning

-   Should roster imports be versioned?
-   What happens if lecturer uploads a corrected CSV?
-   How do we preserve attendance history across roster changes?

------------------------------------------------------------------------

## 6. Scalability Questions

-   Expected max students per session?
-   Concurrency behavior during check-ins?
-   Rate limiting required?

------------------------------------------------------------------------

## 7. Reporting Architecture

-   Should reports be generated via Celery?
-   When are reports triggered?
-   Where are reports stored?

------------------------------------------------------------------------

## 8. Technical Stack Decisions Pending

-   Final backend framework decision?
-   Database type?
-   Caching layer?
-   Deployment environment?

------------------------------------------------------------------------

## 9. UX Clarifications Needed

-   Should flagged students see their flagged state immediately?
-   Should lecturer override flagged logs individually?
-   Should students see historical attendance trends?

------------------------------------------------------------------------

END OF DOCUMENT
