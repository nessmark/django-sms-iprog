# IT 120 – Integrative Programming and Technologies
## Group Laboratory/Assignment: Build a Django Application for Sending SMS (Powered by IPROG SMS API)

**Repository:** https://github.com/nessmark/django-sms-iprog
**Submitted by:** Nesmark Villocino

> **Note for the instructor:** This README serves as a review guide for the project. It covers the system's purpose, architecture, and the exact steps needed to run and evaluate the application locally. Live SMS delivery requires an IPROG SMS API token, which is intentionally excluded from version control; when no token is present the application automatically runs in a safe simulation mode, so every workflow can still be evaluated without credentials.

---

### Table of Contents
1. [Project Overview & Objectives](#1-project-overview--objectives)
2. [Group Members & Assigned Responsibilities](#2-group-members--assigned-responsibilities)
3. [Architecture & System Workflow](#3-architecture--system-workflow)
4. [Key Features & Implemented Enhancements](#4-key-features--implemented-enhancements)
5. [Technologies & Dependencies](#5-technologies--dependencies)
6. [Reviewing the Project Locally](#6-reviewing-the-project-locally)
7. [SMS Provider Configuration (IPROG SMS)](#7-sms-provider-configuration-iprog-sms)
8. [Accessing the Application](#8-accessing-the-application)
9. [Automated Testing & Results](#9-automated-testing--results)
10. [Submission vs Delivery Status Handling](#10-submission-vs-delivery-status-handling)
11. [Known Limitations & Future Roadmap](#11-known-limitations--future-roadmap)

---

### 1. Project Overview & Objectives

This web application was engineered for **IT 120 – Integrative Programming and Technologies**. Its primary objective is to demonstrate enterprise-grade integration between the **Django** Python web framework and an external SMS Gateway API.

While the original laboratory guide outlined integration using Twilio, this project implements the Philippine-focused **IPROG SMS API** (`iprogsms.com`). The implementation includes native phone number formatting (Philippine `09...` and international `+639...` / E.164), secure API key management, real-time message segment calculation, an interactive handset preview, and persistent transmission auditing.

#### Core Learning Objectives Achieved:
1. **Django Web Application Development:** Built with clean Model-View-Template (MVT) architecture, CSRF protection, and separation of concerns.
2. **External SMS Gateway API Integration:** Secure, resilient RESTful HTTP POST communication with the IPROG SMS API, including timeout and error handling.
3. **Rigorous Input Validation:** Real-time and server-side sanitation of phone numbers, character bounds, and message payload integrity.
4. **Credential Security Practices:** Environment variable isolation via `.env` and `python-dotenv`, preventing credential exposure in Git.
5. **Quality Assurance & Testing:** An automated test suite covering edge cases, network failures, credential issues, and validation states.

---

### 2. Group Members & Assigned Responsibilities

| Role / Domain | Assigned Responsibility | Lead Contributor |
| :--- | :--- | :--- |
| **Member 1: Architecture & Backend** | Django project structure, settings, database models (`SMSMessage`, `Contact`, `QuickTemplate`), database migrations, URL routing, and view controllers. | **Nesmark Villocino** |
| **Member 2: Frontend, UX & Validation** | User interface design (Bootstrap 5), interactive live handset preview mockup, form input validation, real-time character & segment counter, toast notifications. | **Nesmark Villocino** |
| **Member 3: Provider Integration & DevOps** | IPROG SMS REST API service wrapper (`IprogSMSService`), simulation/sandbox engine, error/exception recovery, security isolation, automated test suite, and Git repository management. | **Nesmark Villocino** |

> *Note: For this project submission, all three suggested functional roles were consolidated and fully implemented by Nesmark Villocino.*

---

### 3. Architecture & System Workflow

```
[ User Browser ]
       │
       ▼
 [ Django Form ] ──► (Input Validation: Phone E.164 regex, Non-empty message)
       │
       ▼
 [ IprogSMSService ]
       │
       ├──► [ Mode Check ]
       │         │
       │         ├── If Simulation / No Token ──► (Simulate Gateway Response & Reference ID)
       │         │
       │         └── If Live API Token ───────► (HTTP POST https://www.iprogsms.com/api/v1/sms_messages)
       │                                                 │
       │                                                 ▼
       │                                          [ IPROG SMS Gateway ]
       │                                                 │
       │                                                 ▼
       │                              [ Globe / TM / DITO carriers ]
       ▼
[ SQLite Database Log ] ──► Status: SUBMITTED / DELIVERED / FAILED / SIMULATED
       │
       ▼
 [ Django View & UI ] ──► User Feedback (Success / Error Alert & Audit History)
```

---

### 4. Key Features & Implemented Enhancements

#### A. Core Mandatory Features
- **SMS Composition Form:** Clean interface with recipient phone number, message body input, and submission button.
- **IPROG SMS Gateway Integration:** Form-encoded HTTP POST sending payload to `https://www.iprogsms.com/api/v1/sms_messages`.
- **E.164 & Philippine Number Sanitation:** Automatically normalizes `09171234567`, `9171234567`, `639171234567`, and international formats into the standard `+639171234567`.
- **Comprehensive Error Handling:** Gracefully captures missing fields, malformed phone numbers, provider timeouts, DNS failures, and API 4xx/5xx responses without exposing sensitive credentials.
- **CSRF & Security Isolation:** Django CSRF token enforcement on all forms.

#### B. Additional Value-Added Features (Exceeding Rubric Requirements)
1. **SMS Transmission History & Audit Trail:** A persistent SQLite record for every dispatch containing status, timestamp, gateway message ID, and the full raw API response.
2. **Live Interactive Phone Mockup:** A visual smartphone screen on the compose page that updates in real time as recipient numbers and message text are entered.
3. **Live Character Counter & SMS Segment Calculator:** A real-time indicator computing character count (160 GSM-7 / 70 Unicode) and multi-part SMS concatenation segments.
4. **Built-in Address Book / Contact Management:** Saved recipients (Name, Phone, Email, Notes) with one-click auto-population into the compose form.
5. **Analytics & Metrics Dashboard:** Visual cards displaying total messages, gateway submissions, sandbox simulations, failures, and the gateway submission success rate.
6. **Quick Message Templates:** Click-to-insert buttons for common messages (Course Notices, OTP Security Verification, Deadlines, and API Test).
7. **Zero-Cost Simulation / Sandbox Mode:** Allows full evaluation of the workflow without consuming paid SMS credits or configuring an API token.

---

### 5. Technologies & Dependencies

- **Language:** Python 3.10+ (tested on Python 3.14)
- **Web Framework:** Django 6.1 (LTS Architecture)
- **HTTP Client:** Requests 2.34+ (for RESTful API transmission)
- **Configuration Management:** python-dotenv 1.2+
- **Database:** SQLite3 (Django default)
- **Frontend & Styling:** Bootstrap 5.3, Bootstrap Icons 1.11, Google Plus Jakarta Sans font
- **Version Control:** Git & GitHub

---

### 6. Reviewing the Project Locally

The following steps reproduce the development environment. The commands work on macOS, Linux, and Windows.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/nessmark/django-sms-iprog.git
cd django-sms-iprog
```

#### Step 2: Create and Activate a Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

#### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Prepare the Environment File
The repository ships with `.env.example`; the real `.env` is excluded from Git for security.
```bash
cp .env.example .env
```
Section 7 lists the expected keys. Leaving `IPROG_API_TOKEN` empty enables simulation mode.

#### Step 5: Run Database Migrations
```bash
python manage.py migrate
```

#### Step 6: Seed Initial Sample Data (Recommended)
This pre-populates realistic sample contacts (Instructor, College Dept) and quick templates used in the interface:
```bash
python manage.py seed_data
```

---

### 7. SMS Provider Configuration (IPROG SMS)

IPROG SMS (`iprogsms.com`) is a Philippine SMS gateway that delivers through the official Globe, TM, and DITO routes using its shared sender name. It was selected as the provider because foreign gateways are commonly blocked by Philippine carriers.

The project uses a verified IPROG **student account**, which includes **5 free SMS credits** and free daily test SMS. The API token is stored only in `.env` and is never committed to the repository.

#### Expected `.env` Values:
```ini
# Django Settings
DEBUG=True
SECRET_KEY=replace-with-a-secure-random-key
ALLOWED_HOSTS=127.0.0.1,localhost

# IPROG SMS Provider (Active)
IPROG_API_TOKEN=
IPROG_API_URL=https://www.iprogsms.com/api/v1/sms_messages
IPROG_STATUS_URL=https://www.iprogsms.com/api/v1/sms_messages/status

# Simulation Toggle:
# False -> sends for real through IPROG when a token is present.
# True  -> forces simulation mode without sending any real SMS.
SMS_SIMULATION_MODE=False
```

> **Simulation fallback:** With an empty `IPROG_API_TOKEN` (or `SMS_SIMULATION_MODE=True`), the application records the dispatch as `SIMULATED` and returns a reference ID, allowing the full workflow to be reviewed without credits.

#### Network Coverage:
- The shared sender supports **Globe, TM, DITO, and GOMO**.
- **Smart and TNT** numbers require an approved custom sender name from the provider.
- Free daily test SMS is also available; it has a 100-character limit and a branded footer.

---

### 8. Accessing the Application

With the development server running (`python manage.py runserver`), the following pages are available:

- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Transmission History:** [http://127.0.0.1:8000/history/](http://127.0.0.1:8000/history/)
- **Analytics Dashboard:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Address Book:** [http://127.0.0.1:8000/contacts/](http://127.0.0.1:8000/contacts/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

> **Admin access:** For security, the demo superuser credentials are supplied separately with the submission. A local administrator can also be created with `python manage.py createsuperuser`.

---

### 9. Automated Testing & Results

The application includes an automated unit and integration test suite located in `sms_app/tests.py`.

#### Running the Test Suite:
```bash
python manage.py test
```

#### Test Cases Verified:
| # | Test Case Description | Tested Scenario | Expected Result | Result |
| :-: | :--- | :--- | :--- | :---: |
| 1 | **Valid Phone & Message Submission** | Complete form submission with a valid Philippine number | Dispatches request, creates gateway record, status `SUBMITTED` | **PASSED** |
| 2 | **Empty Phone Number** | Submission with a blank recipient field | Rejects submission, displays validation alert | **PASSED** |
| 3 | **Empty Message** | Submission with a blank or whitespace-only message | Rejects submission, displays validation alert | **PASSED** |
| 4 | **Invalid Phone Number Format** | Alphabetic strings or short numeric strings | Caught by E.164 regex, form rejected with error | **PASSED** |
| 5 | **Missing / Invalid API Key** | Invalid provider token response | Handled cleanly without revealing the sensitive token | **PASSED** |
| 6 | **Provider Network Outage** | ConnectionError / DNS failure simulation | Displays a friendly network failure alert | **PASSED** |
| 7 | **Gateway Timeout** | Request timeout simulation (>12s) | Displays a clear timeout notification | **PASSED** |
| 8 | **Submission vs Delivery Distinction** | Successful HTTP 200 from IPROG SMS | Correctly sets status to `SUBMITTED` (no false delivery claim) | **PASSED** |
| 9 | **Live Character & Segment Counter** | 160-char GSM-7 and Unicode payloads | Computes the exact segment split (160 vs 153 chars) | **PASSED** |
| 10 | **Address Book CRUD** | Creating, listing, and deleting contacts | Contact stored, linked, and deleted successfully | **PASSED** |

#### Test Execution Output:
```text
Found 33 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................
----------------------------------------------------------------------
Ran 33 tests in 0.072s

OK
Destroying test database for alias 'default'...
```

---

### 10. Submission vs Delivery Status Handling

As mandated by Section VI of the project guidelines:
> *"A successful API request does not necessarily mean the message has been delivered. The application must distinguish between submission and confirmed delivery when reporting status."*

The application rigorously adheres to this:
1. **Submitted (`SUBMITTED`):** The IPROG SMS API accepted the REST payload and queued it with upstream cellular providers. The UI explicitly states: *"Message successfully submitted to IPROG SMS gateway (Status: Submitted). Delivery to handset is subject to cellular carrier availability."*
2. **Confirmed Delivered (`DELIVERED`):** Set only when the provider's status endpoint reports `completed` (or a carrier delivery receipt confirms it).
3. **Failed (`FAILED`):** Logged when the API returns an error code (invalid token, insufficient balance, network timeout).
4. **Simulated (`SIMULATED`):** Explicitly marked when dispatched under testing/demo mode to avoid misleading users.

The **Check Delivery Status** button on a message's detail page polls IPROG's
`/api/v1/sms_messages/status` endpoint and promotes a record from `SUBMITTED` to
`DELIVERED` (or `FAILED`) only when the provider confirms it.

---

### 11. Known Limitations & Future Roadmap

1. **Two-Way Inbound SMS (MO):** The current version focuses on outbound (MT) SMS dispatching. Inbound SMS replies can be integrated in future phases via an IPROG webhook listener endpoint.
2. **Delivery Receipts (DLR) Webhooks:** Handset delivery confirmations are currently tracked via the gateway status endpoint; asynchronous carrier DLR callbacks can be configured on a public HTTPS server (e.g. using ngrok during local development).
3. **Bulk SMS Scheduler:** Future updates can integrate Celery and Redis to schedule automated mass SMS dispatches at specified times.
