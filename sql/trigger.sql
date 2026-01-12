CREATE OR REPLACE FUNCTION demo.notify_table_update() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify(TG_ARGV[0], row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER coqley_account_data_trigger
AFTER INSERT OR UPDATE ON demo.coqley_account_data
FOR EACH ROW EXECUTE FUNCTION demo.notify_table_update('account-data-channel');

CREATE TRIGGER coqley_payroll_data_trigger
AFTER INSERT OR UPDATE ON demo.coqley_payroll_data
FOR EACH ROW EXECUTE FUNCTION demo.notify_table_update('payroll-data-channel');
