# EELAP -- Electronic Engineering Labs Attendance Platform

## Technical Specification Document (v1.0)

------------------------------------------------------------------------

## 1. Project Overview

EELAP is a lecturer-driven attendance management platform designed for
university electronic laboratory sessions.
It enables structured student roster configuration and secure runtime
attendance sessions with fraud-flagging via geolocation.

The system has two primary actors:

-   Lecturer
-   Student

The platform operates in two main phases:

1.  Configuration Phase
2.  Runtime (Attendance) Phase

------------------------------------------------------------------------

## 2. Configuration Phase

### 2.1 Lecturer Configuration

#### Objective

Establish a validated and grouped source-of-truth roster for a lab
series.

#### Input

A CSV file containing: - Full Name - Email (unique identifier) -
Registration Number (optional but recommended) - Program/Course (Bio,
Electrical, Computer & Communications, etc.) - Gender - Any additional
required institutional identifiers

#### Processing Steps

1.  CSV structure validation
2.  Duplicate detection (email/reg number)
3.  Grouping Logic:
    -   Split by program
    -   Allocate into balanced groups (e.g., bio1, bio2, comp1, comp2)
    -   Enforce gender balance where possible
    -   Respect maximum group capacity
4.  Append generated group label to each student record

#### Post-Processing

-   Lecturer may:
    -   Move students between groups (with constraints)
    -   Remove students
    -   Resolve validation warnings
-   Once confirmed, the roster is LOCKED and becomes the official
    database record.

#### Definition of Done

-   A clean, validated roster stored in the database
-   All students assigned to exactly one group
-   No duplicates
-   Roster marked as immutable (versioned if necessary)

------------------------------------------------------------------------

### 2.2 Student Account Redemption

#### Objective

Allow students to activate their accounts.

#### Flow

1.  Student enters email.
2.  System verifies email exists in locked roster.
3.  OTP email sent.
4.  Student verifies OTP.
5.  Student sets password.
6.  Account becomes active.

#### Definition of Done

-   Student can authenticate successfully.
-   Student sees dashboard.
-   Account linked to roster entry.

------------------------------------------------------------------------

## 3. Runtime Attendance System

### 3.1 Lecturer Flow

1.  Lecturer opens attendance session.

2.  System generates rotating attendance code (refresh interval \~60
    seconds).

3.  Students can only submit check-ins while session is open.

4.  Session auto-closes at configured end time.

5.  System generates summary:

    -   Attended (Clean)
    -   Flagged (Geo out-of-bounds)
    -   Absent (No check-in)

6.  Lecturer reviews.

7.  Lecturer locks and commits results.

8.  Attendance state is permanently recorded.

#### Attendance States (Pre-Commit)

-   CLEAN
-   FLAGGED
-   ABSENT

#### Attendance States (Post-Commit)

-   ATTENDED
-   MISSED

------------------------------------------------------------------------

### 3.2 Student Flow

1.  Student logs in.
2.  Student sees live session (if available).
3.  Student enters rotating code.
4.  System records:
    -   Timestamp
    -   Coordinates
    -   Code validity
5.  Student receives immediate feedback (success or pending if flagged).

------------------------------------------------------------------------

## 4. Fraud Detection (Geo-Flagging)

Each lab has a predefined coordinate (latitude, longitude).

For each check-in:

-   Capture student device coordinates.
-   Compute distance from lab coordinate.
-   If distance **>** threshold → mark as FLAGGED.
-   If within threshold → mark as CLEAN.

No automatic punishment occurs. Lecturer decides final outcome.

------------------------------------------------------------------------

## 5. Core Data Entities (Conceptual)

-   Lecturer
-   Student
-   Roster
-   Group
-   LabSeries
-   AttendanceSession
-   CheckIn
-   AttendanceRecord

------------------------------------------------------------------------

## 6. Background Jobs (Future Scope)

-   Weekly compliance report generation
-   Attendance statistics per student/group
-   Flag frequency analysis

------------------------------------------------------------------------

## 7. Security Considerations

-   OTP-based email verification
-   Password hashing
-   Role-based access control
-   Session-based rotating codes
-   Audit logs for session commits

------------------------------------------------------------------------

## 8. Non-Goals (v1)

-   Automated disciplinary action
-   Advanced AI fraud scoring
-   Multi-campus federation

------------------------------------------------------------------------

END OF DOCUMENT
