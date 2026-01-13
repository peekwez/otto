# CFO Data Model Documentation
This document describes each table in the `demo` schema and shows sample rows.

## dim_time
**Type:** Dimension table (business entities)
**Example rows:**
| date       | fiscal_month   | fiscal_quarter   |   fiscal_year | is_month_end   |
|:-----------|:---------------|:-----------------|--------------:|:---------------|
| 2024-01-01 | 2024-01        | Q1               |          2024 | False          |
| 2024-01-02 | 2024-01        | Q1               |          2024 | False          |
| 2024-01-03 | 2024-01        | Q1               |          2024 | False          |
| 2024-01-04 | 2024-01        | Q1               |          2024 | False          |
| 2024-01-05 | 2024-01        | Q1               |          2024 | False          |

## dim_vendor
**Type:** Dimension table (business entities)
**Example rows:**
|   vendor_id | vendor_name   | category    | payment_terms   | contract_id   |
|------------:|:--------------|:------------|:----------------|:--------------|
|           1 | Google Cloud  | Cloud       | Net30           | C123          |
|           2 | Meta Ads      | Advertising | Net15           | M456          |
|           3 | Accenture     | Consulting  | Net45           | A789          |

## fact_budget_monthly
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| fiscal_month   |   account_id |   dept_id | project_id   | currency_code   |   amount_local |   amount_base | version     |
|:---------------|-------------:|----------:|:-------------|:----------------|---------------:|--------------:|:------------|
| 2024-01        |          101 |        10 |              | USD             |           4703 |          4703 | BUDGET_2024 |
| 2024-01        |          101 |        20 |              | USD             |           1051 |          1051 | BUDGET_2024 |
| 2024-01        |          101 |        30 |              | USD             |           8493 |          8493 | BUDGET_2024 |
| 2024-01        |          201 |        10 |              | USD             |           9935 |          9935 | BUDGET_2024 |
| 2024-01        |          201 |        20 |              | USD             |           7323 |          7323 | BUDGET_2024 |

## dim_currency
**Type:** Dimension table (business entities)
**Example rows:**
| currency_code   |   fx_to_usd | valid_from   | valid_to   |
|:----------------|------------:|:-------------|:-----------|
| USD             |       1     | 2024-01-01   | 2024-12-31 |
| EUR             |       1.1   | 2024-01-01   | 2024-12-31 |
| TRY             |       0.034 | 2024-01-01   | 2024-12-31 |

## dim_account
**Type:** Dimension table (business entities)
**Example rows:**
|   account_id | account_name          | account_type   | rollup_group   |
|-------------:|:----------------------|:---------------|:---------------|
|          101 | Revenue Subscriptions | Revenue        | Topline        |
|          201 | COGS Cloud Hosting    | COGS           | Hosting        |
|          301 | Opex Marketing        | Opex           | Marketing      |
|          302 | Opex IT Software      | Opex           | IT             |

## fact_gl_actuals_monthly
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| fiscal_month   |   account_id |   dept_id | project_id   | currency_code   |   amount_local |   amount_base |
|:---------------|-------------:|----------:|:-------------|:----------------|---------------:|--------------:|
| 2024-01        |          101 |        10 |              | USD             |           5484 |          5484 |
| 2024-01        |          101 |        20 |              | USD             |           1158 |          1158 |
| 2024-01        |          101 |        30 |              | USD             |           4419 |          4419 |
| 2024-01        |          201 |        10 |              | USD             |           3189 |          3189 |
| 2024-01        |          201 |        20 |              | USD             |           5323 |          5323 |

## dim_org
**Type:** Dimension table (business entities)
**Example rows:**
|   org_id |   dept_id | dept_name       | cost_center   | vp          | function   |
|---------:|----------:|:----------------|:--------------|:------------|:-----------|
|        1 |        10 | Marketing North | CC100         | Alice Smith | Marketing  |
|        2 |        20 | IT Infra        | CC200         | Bob Lee     | IT         |
|        3 |        30 | Finance Ops     | CC300         | Carol Tan   | Finance    |

## fact_cash_balance_daily
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| date       |   bank_account_id |   cash_in |   cash_out |   ending_cash |
|:-----------|------------------:|----------:|-----------:|--------------:|
| 2024-01-01 |                 1 |      2538 |       3270 |         99268 |
| 2024-01-02 |                 1 |      4258 |       4446 |         99080 |
| 2024-01-03 |                 1 |      3416 |        776 |        101720 |
| 2024-01-04 |                 1 |       270 |       4785 |         97205 |
| 2024-01-05 |                 1 |       983 |       4335 |         93853 |

## fact_open_commitments
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| po_id   |   vendor_id |   dept_id |   account_id |   total_value |   spent_to_date |   remaining_commitment | expected_spend_month   |
|:--------|------------:|----------:|-------------:|--------------:|----------------:|-----------------------:|:-----------------------|
| PO1     |           1 |        10 |          301 |         50000 |           12000 |                  38000 | 2024-05                |
| PO2     |           2 |        20 |          302 |         80000 |           40000 |                  40000 | 2024-06                |

## dim_project
**Type:** Dimension table (business entities)
**Example rows:**
|   project_id | name                   |   owner_dept | capex_flag   |
|-------------:|:-----------------------|-------------:|:-------------|
|         1001 | Data Warehouse Upgrade |           20 | True         |
|         1002 | Website Redesign       |           10 | False        |

## fact_capex_schedule
**Type:** Fact table (numeric / time-based records)
**Example rows:**
|   project_id |   dept_id | asset_class   | planned_month   |   planned_amount | status   | can_delay   |   delay_sensitivity_days |
|-------------:|----------:|:--------------|:----------------|-----------------:|:---------|:------------|-------------------------:|
|         1001 |        20 | Servers       | 2024-04         |            20000 | Planned  | True        |                       90 |
|         1001 |        20 | Servers       | 2024-07         |            30000 | Planned  | True        |                       90 |

## fact_ap_invoices
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| invoice_id   |   vendor_id |   dept_id |   account_id | invoice_date   | due_date   |   amount | status   | payment_date   | payment_method   |
|:-------------|------------:|----------:|-------------:|:---------------|:-----------|---------:|:---------|:---------------|:-----------------|
| INV001       |           1 |        10 |          301 | 2024-01-15     | 2024-02-15 |    15000 | open     |                | wire             |
| INV002       |           2 |        20 |          302 | 2024-01-20     | 2024-02-20 |    25000 | paid     | 2024-02-18     | ach              |

## fact_ar_invoices
**Type:** Fact table (numeric / time-based records)
**Example rows:**
|   customer_id | invoice_date   | due_date   |   amount | status   | cash_applied_date   |
|--------------:|:---------------|:-----------|---------:|:---------|:--------------------|
|           100 | 2024-01-10     | 2024-02-10 |    30000 | open     |                     |

## fact_marketing_spend_detail
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| fiscal_month   |   dept_id |   account_id | campaign_id   | channel    |   amount |
|:---------------|----------:|-------------:|:--------------|:-----------|---------:|
| 2024-01        |        10 |          301 | CMP001        | Search Ads |     8000 |
| 2024-02        |        10 |          301 | CMP002        | Social Ads |    12000 |

## fact_payroll_runs
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| period_start   | period_end   | pay_date   |   dept_id |   gross_pay |   taxes |   benefits |   contractor_cost |   capitalized_labor |
|:---------------|:-------------|:-----------|----------:|------------:|--------:|-----------:|------------------:|--------------------:|
| 2024-01-01     | 2024-01-15   | 2024-01-20 |        10 |       50000 |   10000 |       5000 |              2000 |                   0 |
| 2024-01-01     | 2024-01-15   | 2024-01-20 |        20 |       60000 |   12000 |       6000 |              3000 |                   0 |

## fact_it_cloud_costs
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| fiscal_month   | provider   | service   | env   |   dept_id |   project_id |   amount |
|:---------------|:-----------|:----------|:------|----------:|-------------:|---------:|
| 2024-01        | GCP        | BigQuery  | prod  |        20 |         1001 |     9000 |

## fact_redistributions_journal
**Type:** Fact table (numeric / time-based records)
**Example rows:**
| journal_id   |   from_account |   to_account |   from_dept |   to_dept |   amount | effective_month   | memo                |
|:-------------|---------------:|-------------:|------------:|----------:|---------:|:------------------|:--------------------|
| JR001        |            301 |          302 |          10 |        20 |     5000 | 2024-02           | Reclass for project |

## kpi_definitions
**Type:** Supporting / KPI / Reporting layer
**Example rows:**
|   kpi_id | name      | formula_sql   | filters_json   | owner   | display_format   |
|---------:|:----------|:--------------|:---------------|:--------|:-----------------|
|        1 | Burn Rate | SELECT ...    | {}             | CFO     | $                |

## kpi_monthly
**Type:** Supporting / KPI / Reporting layer
**Example rows:**
| fiscal_month   |   kpi_id |   value | notes             |
|:---------------|---------:|--------:|:------------------|
| 2024-01        |        1 |   50000 | Seasonal increase |

## metric_targets
**Type:** Supporting / KPI / Reporting layer
**Example rows:**
|   kpi_id | fiscal_month   |   target_value | traffic_light_thresholds   |
|---------:|:---------------|---------------:|:---------------------------|
|        1 | 2024-01        |          45000 | {low:40000,high:60000}     |

## report_templates
**Type:** Supporting / KPI / Reporting layer
**Example rows:**
|   template_id | type          | jinja_template        | chart_specs_json   | style_tokens   |
|--------------:|:--------------|:----------------------|:-------------------|:---------------|
|             1 | board_summary | {{ company }} summary | {}                 | {}             |

## commentary_library
**Type:** Supporting / KPI / Reporting layer
**Example rows:**
|   block_id | topic   | tone    | text_md               | placeholders   |
|-----------:|:--------|:--------|:----------------------|:---------------|
|          1 | cash    | neutral | Cash position stable. | {}             |

## Entity Relationship Diagram (ERD)
```mermaid
erDiagram
    commentary_library {
        PK block_id int NOT NULL
        topic text
        tone text
        text_md text
        placeholders text
    }
    dim_account {
        PK account_id int NOT NULL
        account_name text
        account_type text
        rollup_group text
    }
    dim_currency {
        currency_code text
        fx_to_usd numeric
        valid_from date
        valid_to date
    }
    dim_org {
        org_id int
        PK dept_id int NOT NULL
        dept_name text
        cost_center text
        vp text
        function text
    }
    dim_project {
        PK project_id int NOT NULL
        name text
        owner_dept int
        capex_flag boolean
    }
    dim_time {
        PK date date NOT NULL
        fiscal_month text
        fiscal_quarter text
        fiscal_year int
        is_month_end boolean
    }
    dim_vendor {
        PK vendor_id int NOT NULL
        vendor_name text
        category text
        payment_terms text
        contract_id text
    }
    fact_ap_invoices {
        invoice_id text
        vendor_id int
        dept_id int
        account_id int
        invoice_date date
        due_date date
        amount numeric
        status text
        payment_date date
        payment_method text
    }
    fact_ar_invoices {
        customer_id int
        invoice_date date
        due_date date
        amount numeric
        status text
        cash_applied_date date
    }
    fact_budget_monthly {
        fiscal_month text
        account_id int
        dept_id int
        project_id int
        currency_code text
        amount_local numeric
        amount_base numeric
        version text
    }
    fact_capex_schedule {
        project_id int
        dept_id int
        asset_class text
        planned_month text
        planned_amount numeric
        status text
        can_delay boolean
        delay_sensitivity_days int
    }
    fact_cash_balance_daily {
        date date
        bank_account_id int
        cash_in numeric
        cash_out numeric
        ending_cash numeric
    }
    fact_gl_actuals_monthly {
        fiscal_month text
        account_id int
        dept_id int
        project_id int
        currency_code text
        amount_local numeric
        amount_base numeric
    }
    fact_it_cloud_costs {
        fiscal_month text
        provider text
        service text
        env text
        dept_id int
        project_id int
        amount numeric
    }
    fact_marketing_spend_detail {
        fiscal_month text
        dept_id int
        account_id int
        campaign_id text
        channel text
        amount numeric
    }
    fact_open_commitments {
        po_id text
        vendor_id int
        dept_id int
        account_id int
        total_value numeric
        spent_to_date numeric
        remaining_commitment numeric
        expected_spend_month text
    }
    fact_payroll_runs {
        period_start date
        period_end date
        pay_date date
        dept_id int
        gross_pay numeric
        taxes numeric
        benefits numeric
        contractor_cost numeric
        capitalized_labor numeric
    }
    fact_redistributions_journal {
        journal_id text
        from_account int
        to_account int
        from_dept int
        to_dept int
        amount numeric
        effective_month text
        memo text
    }
    kpi_definitions {
        PK kpi_id int NOT NULL
        name text
        formula_sql text
        filters_json text
        owner text
        display_format text
    }
    kpi_monthly {
        fiscal_month text
        kpi_id int
        value numeric
        notes text
    }
    metric_targets {
        kpi_id int
        fiscal_month text
        target_value numeric
        traffic_light_thresholds text
    }
    report_templates {
        PK template_id int NOT NULL
        type text
        jinja_template text
        chart_specs_json text
        style_tokens text
    }

    fact_gl_actuals_monthly ||--o{ dim_account : "account_id -> account_id"
    fact_gl_actuals_monthly ||--o{ dim_org : "dept_id -> dept_id"
    fact_budget_monthly ||--o{ dim_account : "account_id -> account_id"
    fact_budget_monthly ||--o{ dim_org : "dept_id -> dept_id"
    fact_open_commitments ||--o{ dim_vendor : "vendor_id -> vendor_id"
    fact_open_commitments ||--o{ dim_org : "dept_id -> dept_id"
    fact_open_commitments ||--o{ dim_account : "account_id -> account_id"
    fact_capex_schedule ||--o{ dim_project : "project_id -> project_id"
    fact_capex_schedule ||--o{ dim_org : "dept_id -> dept_id"
    fact_ap_invoices ||--o{ dim_vendor : "vendor_id -> vendor_id"
    fact_ap_invoices ||--o{ dim_org : "dept_id -> dept_id"
    fact_ap_invoices ||--o{ dim_account : "account_id -> account_id"
    fact_payroll_runs ||--o{ dim_org : "dept_id -> dept_id"
    fact_marketing_spend_detail ||--o{ dim_org : "dept_id -> dept_id"
    fact_marketing_spend_detail ||--o{ dim_account : "account_id -> account_id"
    fact_it_cloud_costs ||--o{ dim_org : "dept_id -> dept_id"
    fact_redistributions_journal ||--o{ dim_account : "from_account -> account_id"
    fact_redistributions_journal ||--o{ dim_account : "to_account -> account_id"
    fact_redistributions_journal ||--o{ dim_org : "from_dept -> dept_id"
    fact_redistributions_journal ||--o{ dim_org : "to_dept -> dept_id"
    kpi_monthly }o--|| kpi_definitions : "kpi_id -> kpi_id"
    metric_targets }o--|| kpi_definitions : "kpi_id -> kpi_id"
```
