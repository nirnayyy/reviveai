-- =====================================================================
-- ReviveAI — PostgreSQL / Supabase Synthetic Seed Data
-- Migration ID: 002_seed_data.sql
-- =====================================================================

INSERT INTO customers (customer_id, name, email, phone, ltv_inr, risk_tier, historical_recovery_rate)
VALUES
    ('cust_enterprise_101', 'Acme FinCorp', 'billing@acmefin.in', '+919811002233', 85000.00, 'VIP', 0.8800),
    ('cust_saas_102', 'CloudScale Technologies', 'ops@cloudscale.io', '+919822334455', 32000.00, 'HIGH_VALUE', 0.7400),
    ('cust_consumer_103', 'Rohan Sharma', 'rohan.sharma@gmail.com', '+919833445566', 4500.00, 'STANDARD', 0.6200),
    ('cust_consumer_104', 'Priya Patel', 'priya.p@outlook.com', '+919844556677', 12500.00, 'STANDARD', 0.7000),
    ('cust_consumer_105', 'Vikram Malhotra', 'v.malhotra@yahoo.co.in', '+919855667788', 1800.00, 'AT_RISK', 0.3500)
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO payments (payment_id, customer_id, amount_inr, currency, method, status, error_code, error_description)
VALUES
    ('pay_seed_101', 'cust_enterprise_101', 55000.00, 'INR', 'card', 'failed', 'BAD_REQUEST_PAYMENT_LIMIT_EXCEEDED', 'Corporate card single-transaction limit exceeded'),
    ('pay_seed_102', 'cust_saas_102', 4999.00, 'INR', 'upi', 'failed', 'BAD_REQUEST_UPI_MANDATE_REVOKED', 'UPI AutoPay mandate limit reached or revoked by user'),
    ('pay_seed_103', 'cust_consumer_103', 1999.00, 'INR', 'card', 'failed', 'BAD_REQUEST_PAYMENT_DECLINED_BY_BANK', 'Insufficient funds in customer account'),
    ('pay_seed_104', 'cust_consumer_104', 2499.00, 'INR', 'card', 'failed', 'BAD_REQUEST_PAYMENT_CARD_EXPIRED', 'Saved card token has expired'),
    ('pay_seed_105', 'cust_consumer_105', 999.00, 'INR', 'card', 'failed', 'BAD_REQUEST_PAYMENT_CARD_STOLEN', 'Card reported lost or stolen by cardholder')
ON CONFLICT (payment_id) DO NOTHING;
