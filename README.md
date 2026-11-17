# IT 120 – Integrative Programming and Technologies
## Group Laboratory/Assignment: Build a Django Application for Sending SMS (Powered by IPROG SMS API)

---

### Table of Contents
1. [Project Overview & Objectives](#1-project-overview--objectives)
2. [Group Members & Assigned Responsibilities](#2-group-members--assigned-responsibilities)
3. [Architecture & System Workflow](#3-architecture--system-workflow)
4. [Key Features & Implemented Enhancements](#4-key-features--implemented-enhancements)
5. [Technologies & Dependencies](#5-technologies--dependencies)
6. [Installation & Setup Instructions](#6-installation--setup-instructions)
7. [Configuring the SMS Provider (IPROG SMS)](#7-configuring-the-sms-provider-iprog-sms)
8. [Running the Application](#8-running-the-application)
9. [Automated Testing Procedures & Test Results](#9-automated-testing-procedures--test-results)
10. [Submission vs Delivery Status Handling](#10-submission-vs-delivery-status-handling)
11. [Known Limitations & Future Roadmap](#11-known-limitations--future-roadmap)
12. [Demonstration Video Guide & Recording Checklist](#12-demonstration-video-guide--recording-checklist)

---

### 1. Project Overview & Objectives

This web application was engineered for **IT 120 – Integrative Programming and Technologies**. The primary objective is to demonstrate enterprise-grade integration between the **Django** Python web framework and an external SMS Gateway API.

While the original laboratory guide outlined integration using Twilio, this solution implements the Philippine-focused **IPROG SMS API** (`iprogsms.com`), providing native phone number formatting (including Philippine mobile networks `09...` and international `+639...` / E.164 formats), secure API key management, real-time message segment calculation, interactive UI handset previews, and persistent transmission auditing.

#### Core Learning Objectives Achieved:
1. **Django Web Application Development:** Built with clean Model-View-Template (MVT) architecture, CSRF protection, and separation of concerns.
2. **External SMS Gateway API Integration:** Secure, resilient RESTful HTTP POST communication with the IPROG SMS API with timeout and error handling.
3. **Rigorous Input Validation:** Real-time and server-side sanitation of phone numbers, character bounds, and message payload integrity.
4. **Credential Security Practices:** Environment variable isolation via `.env` and `python-dotenv`, preventing credential exposure in Git.
5. **Quality Assurance & Testing:** Automated test suite verifying edge cases, network failures, credential issues, and validation states.

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
- **E.164 & Philippine Number Sanitation:** Automatically normalizes `09171234567`, `9171234567`, `639171234567`, and international formats into standard `+639171234567`.
- **Comprehensive Error Handling:** Gracefully captures missing fields, malformed phone numbers, provider timeouts, DNS failures, and API 4xx/5xx responses without exposing sensitive credentials.
- **CSRF & Security Isolation:** Django CSRF token enforcement on all forms.

#### B. Additional Value-Added Features (Exceeding Rubric Requirements)
1. **SMS Transmission History & Audit Trail:** Persistent SQLite record for every dispatch containing status, timestamp, gateway message ID, and full raw API response.
2. **Live Interactive Phone Mockup:** A visual smartphone screen on the compose page that dynamically updates in real-time as the user types recipient numbers and message text.
3. **Live Character Counter & SMS Segment Calculator:** Real-time indicator computing character count (160 GSM-7 / 70 Unicode) and multi-part SMS concatenation segments.
4. **Built-in Address Book / Contact Management:** Save frequently messaged recipients (Name, Phone, Email, Notes) with one-click auto-population into the compose form.
5. **Analytics & Metrics Dashboard:** Visual cards displaying Total Messages, Gateway Submissions, Sandbox Simulations, Failures, and Gateway Submission Success Rate percentage.
6. **Quick Message Templates:** Click-to-insert buttons for common messages (Course Notices, OTP Security Verification, Deadlines, and API Test).
7. **Zero-Cost Simulation / Sandbox Mode:** Allows testing the application without consuming paid SMS credits or when an API key is not yet configured.

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

### 6. Installation & Setup Instructions

Follow these step-by-step instructions to set up the project on any macOS, Linux, or Windows machine:

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
venv\Scripts\Activate.ps1
```

#### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
Copy the provided `.env.example` file to create your local `.env`:
```bash
cp .env.example .env
```

Open `.env` in any text editor and customize the values (see Section 7).

#### Step 5: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 6: Seed Initial Sample Data (Optional but Recommended)
Pre-populate realistic sample contacts (Instructor, College Dept) and quick templates:
```bash
python manage.py seed_data
```

---

### 7. Configuring the SMS Provider (IPROG SMS)

IPROG SMS (`iprogsms.com`) is a Philippine SMS gateway that delivers through the
official Globe, TM, and DITO routes using its shared sender name. It is the active
provider for this project because foreign gateways are commonly blocked by PH carriers.

#### Free Credits for Students:
1. Register at [https://www.iprogsms.com/register](https://www.iprogsms.com/register) using Google, GitHub, or Facebook.
2. Choose **Student** verification and enter your project title, school, course, and team members.
3. Student verification is reviewed automatically, usually within a few minutes.
4. Once approved, **5 free SMS credits** are added and a sender header is approved with them.
5. Open **API Settings**, reveal the token, and copy it.

#### Configuring `.env`:
Open the `.env` file in the project root:
```ini
# Django Settings
DEBUG=True
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

# IPROG SMS Provider (Active)
IPROG_API_TOKEN=paste-your-iprog-api-token-here
IPROG_API_URL=https://www.iprogsms.com/api/v1/sms_messages
IPROG_STATUS_URL=https://www.iprogsms.com/api/v1/sms_messages/status

# Simulation Toggle:
# False -> sends for real through IPROG when the token is set.
# True  -> runs in simulation/demo mode without sending any real SMS.
SMS_SIMULATION_MODE=False
```

> **No token yet?** Leave `IPROG_API_TOKEN` empty and the app automatically runs in
> simulation mode, so you can still demo the full workflow without spending credits.

#### Network Coverage Note:
- The shared sender supports **Globe, TM, DITO, and GOMO**.
- **Smart and TNT** numbers require an approved custom sender name (request it in the dashboard).
- Free daily test SMS is also available; it has a 100-character limit and a branded footer.

> **Security Reminder:** Never commit the `.env` file to GitHub or share API tokens in video recordings. The `.gitignore` file is pre-configured to strictly exclude `.env`.

---

### 8. Running the Application

Start the Django local development server:
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Transmission History:** [http://127.0.0.1:8000/history/](http://127.0.0.1:8000/history/)
- **Analytics Dashboard:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Address Book:** [http://127.0.0.1:8000/contacts/](http://127.0.0.1:8000/contacts/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

### 9. Automated Testing Procedures & Test Results

The application includes an automated unit and integration test suite located in `sms_app/tests.py`.

#### Running the Test Suite:
```bash
python manage.py test
```

#### Test Cases Verified:
| # | Test Case Description | Tested Scenario | Expected Result | Result |
| :-: | :--- | :--- | :--- | :---: |
| 1 | **Valid Phone & Message Submission** | Complete form submission with valid Philippine number | Dispatches request, generates gateway record, status `SUBMITTED` | **PASSED** |
| 2 | **Empty Phone Number** | Submitting with blank recipient field | Rejects submission, displays validation alert | **PASSED** |
| 3 | **Empty Message** | Submitting with blank or whitespace-only message | Rejects submission, displays validation alert | **PASSED** |
| 4 | **Invalid Phone Number Format** | Submitting alphabetic strings or short numeric strings | Caught by E.164 regex, form rejected with error | **PASSED** |
| 5 | **Missing / Invalid API Key** | HTTP 401 Unauthorized gateway response | Catches error cleanly without revealing sensitive key string | **PASSED** |
| 6 | **Provider Network Outage** | ConnectionError / DNS failure simulation | Displays friendly network failure alert | **PASSED** |
| 7 | **Gateway Timeout** | Requests timeout simulation (>12s) | Displays clear timeout notification to user | **PASSED** |
| 8 | **Submission vs Delivery Distinction** | Successful HTTP 200 from IPROG SMS | Correctly sets status to `SUBMITTED` (not claiming false handset delivery) | **PASSED** |
| 9 | **Live Character & Segment Counter** | 160-char GSM-7 and Unicode payload | Computes exact segment split (160 vs 153 chars) | **PASSED** |
| 10 | **Address Book CRUD** | Creating, listing, and deleting contacts | Contact successfully stored, linked, and deleted | **PASSED** |

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
3. **Failed (`FAILED`):** Logged when the API returns an error code (invalid key, insufficient balance, network timeout).
4. **Simulated (`SIMULATED`):** Explicitly marked when dispatched under testing/demo mode to avoid misleading users.

The **Check Delivery Status** button on a message's detail page polls IPROG's
`/api/v1/sms_messages/status` endpoint and promotes a record from `SUBMITTED` to
`DELIVERED` (or `FAILED`) only when the provider confirms it.

---

### 11. Known Limitations & Future Roadmap

1. **Two-Way Inbound SMS (MO):** The current version focuses on outbound (MT) SMS dispatching. Inbound SMS replies can be integrated in future phases via an IPROG webhook listener endpoint.
2. **Delivery Receipts (DLR) Webhooks:** Handset delivery confirmations are currently tracked via gateway submission status; asynchronous carrier DLR callbacks can be configured on a public HTTPS server (e.g. using ngrok during local development).
3. **Bulk SMS Scheduler:** Future updates can integrate Celery and Redis to schedule automated mass SMS dispatches at specified times.

---

### 12. Demonstration Video Guide & Recording Checklist

When recording the **3 to 10-minute demonstration video**, follow this structured walkthrough:

1. **Introduction (1 min):**
   - Introduce yourself (Nesmark Villocino).
   - State the project title: *IT 120 - Django Application for Sending SMS using IPROG SMS API*.
   - Mention the 3 assigned project roles you fulfilled (Architecture/Backend, Frontend/Validation, Gateway Integration/QA).
2. **User Interface Walkthrough (1-2 mins):**
   - Show the Compose SMS interface, clean layout, and the interactive phone mockup.
   - Type a phone number and message to show the real-time character counter and live screen preview updating.
   - Demonstrate the Quick Message Templates and Contact Picker.
3. **SMS Sending Demonstration (1-2 mins):**
   - Enter an authorized recipient test number (e.g., your mobile number).
   - Click "Send SMS via IPROG SMS".
   - Show the green success notification banner highlighting the Gateway Reference ID.
4. **Validation & Error Handling Demonstration (1 min):**
   - Attempt to submit an empty recipient number -> observe the validation message.
   - Attempt to enter invalid characters (e.g., `abc12345`) -> observe format rejection.
   - Attempt to submit a blank message -> observe the required field error.
5. **Additional Features Demonstration (1-2 mins):**
   - Open **Message History**: show search filtering and click "Details" to show the raw JSON response payload from IPROG SMS.
   - Open **Analytics Dashboard**: show total messages, submission success rate, and recent activity.
   - Open **Address Book**: demonstrate adding a contact and clicking "SMS" to auto-populate the form.
6. **Code & Security Summary (1 min):**
   - Show `settings.py` and explain how `IPROG_API_TOKEN` is securely read from `.env` and excluded from `.gitignore`.
   - Run `python manage.py test` in the terminal to demonstrate all 33 automated tests passing cleanly.
   - Conclude the presentation.

---
