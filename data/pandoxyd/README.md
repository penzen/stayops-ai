---
license: cc-by-nc-sa-4.0
---
# Synthetic CRM Seed Data for Concierge & Property Management: GDPR-compliant, realistic market distributions for software testing & demos (SQL/CSV) (DEMO)

Thank you for downloading this synthetic dataset! 

This repository contains a functional, lightweight preview of a 100% synthetic dataset designed for testing real estate CRMs and property management software.

## **>> Full version available [on Gumroad](https://shopoxyd.gumroad.com/l/synthetic-property-management-crm-data) <<** 
> This demo provides a baseline schema. For large-scale stress testing, production database seeding, or advanced ML pipelines, get the full commercial dataset : **70 properties, 4,500 customers, 11,900+ operations, 4,800+ bookings (JSON included**).

---

## 📊 Dataset Volumes & Key Metrics

This package contains 5 fully populated tables representing a high-density operational rental agency ecosystem:
- **15 Premium Properties:** Exclusively located in the Île-de-France region (Paris area), with realistic addresses, surface areas, and pricing models.
- **1035 Multi-National Customers:** A diverse database of clients with international origins, simulated contact details, and logical purchasing power profiles.
- **32 Employees:** Managed with structured internal roles, hierarchy, and assigned regional sectors.
- **1075 Bookings:** One-year reservation histories with realistic seasonality, pricing variations, and check-in/out states.
- **2646 Tasks & Operations:** Granular operational tracking (cleaning, maintenance, concierge requests) linked directly to properties, staff, and bookings.

---

## 🎭 Business Context & Realism Standards

To ensure maximum utility in production-like environments, this dataset avoids rely on flat, uniform randomness. Instead, it was generated using proprietary algorithmic boundaries that simulate the authentic operational behavior of a **Premium Concierge & Luxury Property Management Agency** in the Île-de-France region.

### Key Characteristics:
- **Market-Driven Geographical Clustering:** Property locations and density are statistically weighted to naturally reflect high-demand luxury sectors (Paris intra-muros, Inner & Outer Suburbs aka "Petite & Grande Couronne").
- **Realistic Demographic Skewness:** Client profiles incorporate diverse international origins and logical purchasing power variance, aligning with real-world high-net-worth individual (HNWI) travel patterns.
- **Organic Seasonality:** Reservation and booking frequencies simulate logical annual business peaks (high-season vs. low-season fluctuations).
- **Operational Coherence:** Task and maintenance distributions are dynamically tied to property types and booking lifecycles, ensuring coherent ratios when building analytics dashboards or testing business logic.

*This statistical distribution guarantees the presence of natural data trends and realistic database load properties.*

## 🎯 Primary Use Cases

* **Comprehensive QA & Load Testing:** Instantly populate staging environments, highly connected data to test query performance, indexing, and edge cases.
* **Flawless Client Demonstrations & POCs:** Showcase your application or analytics dashboards with realistic, dense, and non-anonymous looking metrics (proper French postal codes, logical status histories, and realistic commercial interactions).
* **GDPR-Compliant AI & ETL Pipelines:** Train local LLMs, test semantic search algorithms, or build data pipelines without running into privacy regulations or data-masking overhead.

---

## 🔬 Core Quality Standards

* **100% Strict Referential Integrity:** Every Foreign Key (`FK`) maps accurately to a valid Primary Key (`PK`). Zero orphan records across all 5 tables.
* **Algorithmic Coherence:** Temporal constraints are mathematically valid (e.g., interaction timestamps always occur sequentially after a customer account creation date).
* **International & Localized Standardization:** * Full adherence to ISO 8601 (`YYYY-MM-DD HH:MM:SS`) for timestamps.
  * Standardized French localizations for phone numbers, company registration formats, and regional mapping compatible with European business software constraints.
  * Universal `UTF-8` encoding.
* **Absolute Compliance:** Built from the ground up using advanced procedural generators. 100% GDPR-compliant by design, fully compliant with data privacy regulations, and safe for local or cloud environments.

## 🛡️ Compliance & Warnings (GDPR & Synthetic Nature)

This dataset is **100% synthetic** and algorithmically generated. It contains **no real Personally Identifiable Information (PII)** and is fully compliant with **GDPR** and international data privacy regulations.

### Key Security Points:
*   **No Real Persons:** Names, addresses, emails, and phone numbers are procedurally generated. No record corresponds to an existing real-world individual.
*   **Ethical Usage:** This data is provided exclusively for software development, performance testing, technical demonstrations, and academic research.
*   **Prohibition on Identification:** It is strictly forbidden to use this dataset to attempt to identify real individuals, for "doxing," phishing, or any fraudulent activity.
*   **Test Data Only:** This dataset is not intended to be used as a real production database or as a source of truth for critical business decisions.

> **Important Note:** While the data adheres to standard French formats (postal codes, phone number formats), it is entirely fictitious. Any attempt to cross-reference this data with real-world databases is futile and violates the terms of use.

---
## 🔀 Tables, Labels & Relations

The dataset consists of 5 tables that maintain strict referential integrity.

**Properties:**
* `property_id`: Unique identifier for each property in the dataset
* `title`: Descriptive name or headline of the property listing
* `prop_address`: Complete street address of the property
* `postal_code`: Postal or zip code corresponding to the property location
* `department`: Administrative department or region where the property is located
* `city`: Name of the city where the property is situated
* `max_guests`: Maximum number of guests allowed to stay at the property
* `cleaning_fee`: One-time fee charged for cleaning services after checkout
* `base_price`: Standard nightly rate for the property before additional fees
* `prop_type`: Category or classification of the property (e.g., apartment, house, studio)
* `surface`: Total floor area of the property, usually in square meters

**Guests:**
* `guest_id`: Unique identifier for each guest in the system
* `first_name`: Guest's given name
* `last_name`: Guest's family name
* `email`: Primary email address used for communication and booking confirmations
* `phone`: Contact phone number for the guest
* `guest_lang`: Preferred language of the guest for communications
* `locale`: Regional code from where the guest came from
* `guest_geo`: Geographic origin or current location of the guest

**Teams:**
* `team_id`: Unique identifier for each team or staff member record
* `team_group`: Organizational group or department the team member belongs to
* `team_role`: Job title or functional role within the organization
* `first_name`: Team member's given name
* `last_name`: Team member's family or surname
* `gender`: Gender identity of the team member
* `sector`: Business sector or area of specialization
* `languages`: List of languages spoken by the team member
* `managed_by`: Identifier or name of the supervisor or manager for this team member

**Bookings:**
* `booking_id`: Unique identifier for each reservation record
* `guest_id`: Foreign key linking the booking to the specific guest
* `property_id`: Foreign key linking the booking to the specific property
* `check_in`: Scheduled arrival date and time for the guest
* `check_out`: Scheduled departure date and time for the guest
* `nights`: Total number of nights the guest will stay
* `total_price`: Final calculated cost of the reservation including all fees
* `book_status`: Current state of the booking (e.g., confirmed, cancelled, completed)
* `source`: Platform or channel where the booking originated (e.g., website, app, agency)
* `assigned_to`: Team member responsible for managing or overseeing this booking

**Tasks:**
* `task_id`: Unique identifier for each task record
* `property_id`: Foreign key linking the task to a specific property
* `booking_id`: Foreign key linking the task to a specific booking (if applicable)
* `category`: Type or classification of the task (e.g., cleaning, maintenance, check-in)
* `title`: Brief descriptive name of the task
* `task_date`: Scheduled date for task completion
* `task_status`: Current progress state of the task (e.g., pending, in progress, done)
* `assigned_by`: User or system that created and assigned the task
* `assigned_to`: Team member responsible for executing the task
* `parent_task_id`: Identifier of a parent task if this task is a subtask or dependency

**Relations between tables:**

```======================================================================
  RESOURCES                                      OPERATIONAL TABLES
======================================================================

 [properties]  ─────── property_id ─────────► [ bookings ]
               ─────── property_id ───┐       │
                                      │       │
 [guests]      ─────── guest_id ──────┼──────►│ booking_id
                                      │       │
                                      ▼       ▼
 [teams]       ─── team_id (assigned_to/by) ─► [ tasks ]
======================================================================
```
---

## 📂 Schema of files

You can find csv, json and sql files format.

```
/dataset
    ├── LICENSE_demo.md
    ├── README.md
    ├── database_setup_demo.sql
    ├── csv/
    |   ├── bookings_demo.csv
    |   ├── guests_demo.csv
    |   ├── properties_demo.csv
    |   ├── tasks_demo.csv
    |   └── teams_demo.csv
    └── json/
        ├── bookings_demo.json
        ├── guests_demo.json
        ├── properties_demo.json
        ├── tasks_demo.json
        └── teams_demo.json
```

## SQL Compatibility

These SQL schemas are compatible with all modern versions of:

* SQLite: **3.30+**
* MySQL: **5.7+**
* PostgreSQL: **12+**

> *Note:* The schemas use standard SQL types compatible with ANSI SQL. For financial data, FLOAT is used for simplicity, but DECIMAL is recommended for production financial applications.

## SQL Data Importation

You can quickly import sql files into your databases with these commands line from your terminal:

* **MySQL :** `mysql -u [user_name] -p [database_name] < database_setup_demo.sql`
* **PostgreSQL :** `psql -U [user_name] -d [database_name] -f database_setup_demo.sql`
* **SQLite :** `sqlite3 [database_name].db < database_setup_demo.sql`

> **Tip:** Replace `[user_name]` and `[database_name]` with your own credentials / value.

### Quick Start

Use this SQL command to verify the imported dataset into your database software:

`SELECT * FROM bookings WHERE book_status = 'confirmed' LIMIT 5;`

---

## Upgrade to the Full Commercial Dataset

Need more data for large-scale stress testing, production environments, or advanced ML models? The complete premium dataset is available on Gumroad and features:

- **70 Premium Properties**
- **4,500 Multi-National Customers**
- **34 Employees**
- **4,863 Bookings**
- **11,964 Tasks & Operations**
- **Full JSON format included**

👉 **[Get the Full Commercial Dataset on Gumroad](https://shopoxyd.gumroad.com/l/synthetic-property-management-crm-data)**

---

## 📩 Contact

If you have any problem with the product or a suggestion, you can reach me at pandoxyd@gmail.com