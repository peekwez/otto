# Coqley Data Reference Guide

This document provides a comprehensive reference for the Coqley accounting and payroll data tables. Use this as a reference skill for LLM agents to understand the data structure, column meanings, and how to query and analyze these datasets.

## Overview

The Coqley dataset consists of two main tables stored in PostgreSQL (`demo` schema):
1. **coqley_account_data** - Accounting/General Ledger transaction data
2. **coqley_payroll_data** - Employee payroll and compensation data

Both tables contain real business data and are used for financial analysis, reporting, and decision-making.

---

## Table 1: coqley_account_data

**Purpose:** Stores general ledger accounting transactions including debits, credits, account information, and transaction metadata.

**Table Type:** Fact table (transactional data)

**Primary Keys:** None explicitly defined, but `kaid` (transaction ID) and `numrec` (record number) together can uniquely identify rows.

### Column Descriptions

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `comp` | TEXT | YES | Company identifier (e.g., "Q2025") |
| `type` | TEXT | YES | Transaction type (e.g., "JVOPEN" for journal voucher opening balance) |
| `kaid` | BIGINT | YES | **Transaction ID** - Unique identifier for each transaction entry |
| `numrec` | NUMERIC | YES | Record number within a transaction (line item number) |
| `hisab_number` | TEXT | YES | Account number/code (chart of accounts identifier) |
| `date` | TIMESTAMP | YES | **Transaction date** - The date when the transaction occurred |
| `md` | TEXT | YES | Debit/Credit indicator (typically "C" for Credit, "D" for Debit) |
| `m_dollar` | NUMERIC | YES | **Debit amount in USD** - Expenses/Assets increase (money going out/investment) |
| `d_dollar` | NUMERIC | YES | **Credit amount in USD** - Revenue/Liabilities increase (money coming in) |
| `m_ll` | NUMERIC | YES | Debit amount in Lebanese Lira (LL) |
| `d_ll` | NUMERIC | YES | Credit amount in Lebanese Lira (LL) |
| `m_aj` | NUMERIC | YES | Debit amount in adjusted currency |
| `d_aj` | NUMERIC | YES | Credit amount in adjusted currency |
| `shareh` | TEXT | YES | Shareholder or partner identifier |
| `dep` | BIGINT | YES | Department code (organizational unit) |
| `valid_date` | TIMESTAMP | YES | Validation or effective date |
| `job` | NUMERIC | YES | Job/Project identifier |
| `cur1_sarfe` | NUMERIC | YES | Currency exchange rate (sarfe) |
| `bank` | NUMERIC | YES | Bank account identifier |
| `chq` | NUMERIC | YES | Check number |
| `chq_owner` | NUMERIC | YES | Check owner/issuer identifier |
| `opp_acc` | TEXT | YES | Opposite/paired account number |
| `delr` | TEXT | YES | Dealer identifier |
| `group` | NUMERIC | YES | Account group classification |
| `subgroup` | NUMERIC | YES | Account subgroup classification |
| `unit` | NUMERIC | YES | Business unit identifier |
| `brand` | NUMERIC | YES | Brand identifier |
| `family` | NUMERIC | YES | Product family identifier |
| `hisab_name` | TEXT | YES | **Account name** - Human-readable account description (e.g., "Capital", "Result - Profit") |
| `umla_number` | BIGINT | YES | Transaction document number (umla) |

### Key Relationships

- `kaid` groups multiple line items (rows) that belong to the same transaction
- `hisab_number` and `hisab_name` represent the same account (number vs. name)
- `date` is the primary time dimension for transaction analysis
- `m_dollar` (debits) and `d_dollar` (credits) are mutually exclusive per row - typically one is NULL and the other has a value

### Common Analysis Patterns

1. **Account Activity Analysis:**
   - Group by `hisab_name` to see total activity per account
   - Sum `m_dollar` and `d_dollar` separately to get debits vs. credits
   - Calculate net activity: `d_dollar - m_dollar`

2. **Time-Based Analysis:**
   - Use `date` for trend analysis (daily, monthly, quarterly)
   - Filter by date ranges for period comparisons
   - Aggregate by fiscal periods derived from `date`

3. **Transaction Analysis:**
   - Group by `kaid` to see complete transaction details
   - Count unique `kaid` values to get transaction volume
   - Join multiple rows with same `kaid` to see full double-entry details

4. **Account Classification:**
   - Use `hisab_name` to identify account types (Revenue, COGS, Opex, Assets, Liabilities)
   - Group by account categories for P&L or Balance Sheet analysis

### Example Queries

```sql
-- Get top accounts by total activity
SELECT 
    hisab_name,
    SUM(COALESCE(m_dollar, 0) + COALESCE(d_dollar, 0)) as total_activity,
    SUM(COALESCE(d_dollar, 0)) as total_credits,
    SUM(COALESCE(m_dollar, 0)) as total_debits,
    COUNT(DISTINCT kaid) as transaction_count
FROM demo.coqley_account_data
GROUP BY hisab_name
ORDER BY total_activity DESC
LIMIT 20;

-- Monthly revenue trends
SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(COALESCE(d_dollar, 0)) as total_revenue,
    COUNT(DISTINCT kaid) as transactions
FROM demo.coqley_account_data
WHERE hisab_name ILIKE '%revenue%' OR hisab_name ILIKE '%sales%'
GROUP BY month
ORDER BY month;
```

---

## Table 2: coqley_payroll_data

**Purpose:** Stores employee payroll information including compensation, benefits, taxes, attendance, and employee demographics.

**Table Type:** Fact table (employee compensation data)

**Primary Keys:** None explicitly defined, but `sq` (sequence number) may serve as a unique identifier, possibly combined with `month` or `month_num`.

### Column Descriptions

#### Employee Information

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `sq` | BIGINT | YES | Sequence number / Employee record ID |
| `branch` | TEXT | YES | Branch location (e.g., "GEM") |
| `name` | TEXT | YES | **Employee full name** |
| `dep` | TEXT | YES | **Department** - Organizational department (e.g., "Kitchen") |
| `nationality` | TEXT | YES | Employee nationality (e.g., "Lebanese") |
| `position` | TEXT | YES | **Job position/title** (e.g., "Head Chef", "Sous Chef") |
| `grade` | NUMERIC | YES | Job grade level |
| `status` | TEXT | YES | Marital status (e.g., "Married", "Single") |
| `starting_date` | TEXT | YES | **Employment start date** - Can be parsed to calculate tenure |
| `termination` | NUMERIC | YES | Termination date or flag |
| `first` | TEXT | YES | Employee first name |
| `last` | TEXT | YES | Employee last name |
| `dob` | TIMESTAMP | YES | Date of birth |

#### Pay Period Information

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `month_num` | BIGINT | YES | **Month number** (1-12) |
| `month` | TEXT | YES | **Month name** (e.g., "Jan", "Feb") |
| `shift` | TEXT | YES | Shift type (e.g., "Straight") |
| `period` | NUMERIC | YES | Pay period identifier |

#### Compensation and Costs

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `monthly` | NUMERIC | YES | **Monthly base salary** |
| `shift_rate` | NUMERIC | YES | Shift rate multiplier |
| `cost` | NUMERIC | YES | **Total cost per employee** - Often the primary cost metric |
| `net_to_\npay` | BIGINT | YES | **Net pay to employee** (after deductions) - Note: column name has newline |
| `net_to_\npay_n` | BIGINT | YES | Net pay (numeric version) |

#### Taxes and Deductions

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `tax` | NUMERIC | YES | **Income tax amount** |
| `taxed` | TEXT | YES | Tax status indicator ("Y" or "N") |
| `nssf` | NUMERIC | YES | **NSSF (social security) contribution** |
| `ss` | TEXT | YES | Social security indicator |
| `ss_com` | TEXT | YES | Social security company indicator |
| `salary_tax` | BIGINT | YES | Salary tax amount |
| `net_taxed` | NUMERIC | YES | Net taxable amount |
| `taxable_lbp` | NUMERIC | YES | Taxable amount in Lebanese Lira |
| `exemption` | BIGINT | YES | Tax exemption amount |

#### Benefits and Allowances

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `transport` | BIGINT | YES | **Transportation allowance** |
| `family_allowance` | NUMERIC | YES | **Family allowance** benefit |
| `loan` | NUMERIC | YES | Employee loan amount |
| `mobile` | NUMERIC | YES | Mobile phone allowance |
| `s&m` | NUMERIC | YES | Salary and miscellaneous |

#### Attendance Tracking

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `col_1_am` through `col_31_am` | TEXT | YES | **Morning attendance for day 1-31** (values: "Y", "N", "Y/2", "V", "V/2", etc.) |
| `col_1_pm` through `col_31_pm` | TEXT | YES | **Afternoon attendance for day 1-31** (values: "Y", "N", "Y/2", "V", "V/2", etc.) |
| `total\nshifts` | NUMERIC | YES | **Total shifts worked** - Note: column name has newline |
| `total\nattendance` | NUMERIC | YES | **Total attendance days** - Note: column name has newline |
| `vac` | NUMERIC | YES | **Vacation days used** |
| `sick` | BIGINT | YES | **Sick days used** |

#### Taxable Amounts

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `others\ntaxable` | NUMERIC | YES | Other taxable amounts - Note: column name has newline |
| `total\ntaxable` | NUMERIC | YES | **Total taxable amount** - Note: column name has newline |
| `actual_taxable` | NUMERIC | YES | **Actual taxable amount** (may differ from total taxable) |

#### Additional Columns

| Column Name | Data Type | Nullable | Description |
|------------|-----------|----------|-------------|
| `others\n+` | NUMERIC | YES | Other additions - Note: column name has newline |
| `transport.1` | BIGINT | YES | Alternative transport column |
| `f_all` | BIGINT | YES | Family allowance (alternative) |
| `col_0.03`, `col_0.08`, `col_0.085`, `col_0.06` | NUMERIC/BIGINT | YES | Various calculation columns (likely percentages or rates) |
| `nssf_payment` | BIGINT | YES | NSSF payment amount |
| `col_&` | TEXT | YES | Additional reference column |
| `serial` | BIGINT | YES | Serial number |
| `pay` | TEXT | YES | Payment method (e.g., "Bank") |
| `notes` | NUMERIC | YES | Notes or additional information |
| `u`, `n`, `y`, `u.1`, `n.1` | NUMERIC | YES | Various status or calculation flags |
| `check` | NUMERIC | YES | Check number |
| `expense_n` | BIGINT | YES | Expense number |
| `unnamed:_124`, `unnamed:_125` | NUMERIC | YES | Unnamed/placeholder columns |

### Key Relationships

- Each row typically represents one employee's payroll record for one month
- `sq` may uniquely identify employees across months (employee ID)
- `dep` (department) can be used for cost center analysis
- `position` groups employees by job role
- `month` and `month_num` represent the pay period

### Common Analysis Patterns

1. **Department Cost Analysis:**
   - Group by `dep` to see total payroll costs per department
   - Sum `cost` or `monthly` to get total compensation
   - Include `tax`, `nssf`, and benefits for total cost

2. **Position/Role Analysis:**
   - Group by `position` to see cost by job title
   - Calculate average salary by position
   - Count employees per position

3. **Employee-Level Analysis:**
   - Group by `name` or `sq` to see individual employee records
   - Calculate tenure from `starting_date`
   - Track individual compensation over time

4. **Monthly Trends:**
   - Group by `month` or `month_num` for monthly payroll trends
   - Compare month-over-month changes
   - Calculate year-to-date totals

5. **Attendance Analysis:**
   - Use `col_X_am` and `col_X_pm` columns to analyze daily attendance
   - Sum `total\nattendance` and `total\nshifts` for attendance metrics
   - Analyze `vac` and `sick` days usage

6. **Cost Breakdown:**
   - Separate base pay (`monthly`, `cost`) from benefits (`transport`, `family_allowance`)
   - Include employer costs (`nssf`, `tax`) for total cost analysis
   - Calculate net pay vs. gross cost

### Important Notes

- **Column Names with Newlines:** Some columns have literal newline characters (`\n`) in their names:
  - `net_to_\npay`
  - `total\nshifts`
  - `total\nattendance`
  - `others\ntaxable`
  - `total\ntaxable`
  - `others\n+`
  
  When querying these columns in SQL, you may need to use quoted identifiers or handle the newline character.

- **Multiple Cost Columns:** The table has several potential cost columns:
  - `monthly` - Base monthly salary
  - `cost` - Total cost (often the most comprehensive)
  - `net_to_\npay` - Net pay after deductions
  - Use `cost` for employer total cost, `monthly` for base salary, `net_to_\npay` for employee take-home

- **Date Parsing:** `starting_date` is stored as TEXT and needs to be parsed with `pd.to_datetime()` or `TO_TIMESTAMP()` in SQL.

### Example Queries

```sql
-- Department payroll cost summary
SELECT 
    dep as department,
    COUNT(DISTINCT name) as employee_count,
    SUM(COALESCE(cost, monthly, 0)) as total_cost,
    SUM(COALESCE(tax, 0)) as total_taxes,
    SUM(COALESCE(nssf, 0)) as total_nssf,
    AVG(COALESCE(cost, monthly, 0)) as avg_cost_per_employee
FROM demo.coqley_payroll_data
WHERE dep IS NOT NULL
GROUP BY dep
ORDER BY total_cost DESC;

-- Monthly payroll trends
SELECT 
    month,
    month_num,
    COUNT(DISTINCT name) as active_employees,
    SUM(COALESCE(cost, monthly, 0)) as total_monthly_cost,
    SUM(COALESCE(net_to_\npay, 0)) as total_net_pay
FROM demo.coqley_payroll_data
GROUP BY month, month_num
ORDER BY month_num;

-- Position salary analysis
SELECT 
    position,
    COUNT(DISTINCT name) as employee_count,
    AVG(COALESCE(monthly, 0)) as avg_monthly_salary,
    MIN(COALESCE(monthly, 0)) as min_salary,
    MAX(COALESCE(monthly, 0)) as max_salary
FROM demo.coqley_payroll_data
WHERE position IS NOT NULL
GROUP BY position
ORDER BY avg_monthly_salary DESC;
```

---

## Data Usage Guidelines for LLM Agents

### When Analyzing Accounting Data (`coqley_account_data`):

1. **Always filter out rows where both `m_dollar` and `d_dollar` are NULL or zero** - these may be placeholder or incomplete records.

2. **Use `hisab_name` for account-based queries** - it's more human-readable than `hisab_number`.

3. **For revenue analysis**, look for accounts with names containing "Revenue", "Sales", "Income", or positive `d_dollar` values.

4. **For expense analysis**, look for accounts with names containing "Expense", "Cost", "Opex", or positive `m_dollar` values.

5. **Group by `kaid`** to see complete double-entry transactions (one transaction = multiple rows).

6. **Use `date` for time-based analysis** - aggregate by month, quarter, or year as needed.

### When Analyzing Payroll Data (`coqley_payroll_data`):

1. **Use `cost` as the primary cost metric** for employer total cost calculations.

2. **Use `monthly` for base salary** comparisons and averages.

3. **Calculate total cost = base + taxes + benefits** when detailed breakdown is needed:
   - `cost` (or `monthly`) + `tax` + `nssf` + `transport` + `family_allowance`

4. **For employee count**, use `COUNT(DISTINCT name)` or `COUNT(DISTINCT sq)` to avoid double-counting.

5. **Parse `starting_date`** as a date to calculate employee tenure.

6. **Group by `dep`** for department-level analysis.

7. **Group by `position`** for job role analysis.

8. **Use `month_num` for chronological sorting** instead of `month` (text) to ensure proper order.

### Common Join Patterns

While these tables don't have explicit foreign keys, they can be joined on:
- `dep` (department) - if department codes are consistent between tables
- Date fields for time-based correlation

### Best Practices

1. **Handle NULLs explicitly** - Many columns are nullable, use `COALESCE()` or `.fillna()`.

2. **Validate data quality** - Check for empty strings, invalid dates, or unexpected values.

3. **Use appropriate aggregations** - For financial data, prefer `SUM()` for amounts and `COUNT(DISTINCT ...)` for unique entities.

4. **Format currency values** - Round monetary values to 2 decimal places for display.

5. **Consider time periods** - When comparing periods, ensure date ranges are complete and comparable.

6. **Document assumptions** - Note any assumptions about missing data or calculated fields.

---

## Summary

This reference guide provides comprehensive documentation for the Coqley accounting and payroll datasets. Use it as a skill reference for LLM agents to understand the data structure, make appropriate queries, and perform accurate financial analysis.

**Key Takeaways:**
- `coqley_account_data` contains transaction-level accounting data with debits (`m_dollar`) and credits (`d_dollar`)
- `coqley_payroll_data` contains employee-level payroll data with compensation, benefits, and attendance tracking
- Both tables require careful handling of NULLs, date parsing, and column name special characters
- Group by appropriate dimensions (`hisab_name`, `dep`, `position`, `month`) for meaningful analysis
