-- Create data inputs --
INSERT INTO goods_categories (code, label, extra_minutes) VALUES
    ('electronics', 'Electronics', 1.5),
    ('furniture', 'Furniture', 0.5),
    ('clothing_textiles', 'Clothing & Textiles', 0.5),
    ('chemicals', 'Chemicals', 3.0),
    ('food_beverages', 'Food & Beverages', 2.0),
    ('automotive_parts', 'Automotive Parts', 1.0),
    ('machinery_parts', 'Machinery & Parts', 1.0),
    ('plastics', 'Plastics', 0.5),
    ('building_materials', 'Building Materials', 0.5),
    ('paper_products', 'Paper Products', 0.5);

INSERT INTO lanes (lane_number, capacity) VALUES (1, 5), (2, 5), (3, 5), (4, 5), (5, 5);

INSERT INTO admin_windows (window_number) VALUES (1), (2), (3), (4);

INSERT INTO users (username, password_hash, role) VALUES
    ('canopy1',     '$2b$12$FzKloFzCvFFeyRdAyx1obeQOf8ficpzF7UUzx0YJPCqaziHFREc4a',     'canopy1'),
    ('immigration', '$2b$12$4QESgnXD1bvrJQS9t9mKg.DVUyZd1.SdT69bzbgAQSMi0m39Mh1km', 'immigration'),
    ('canopy2',     '$2b$12$YLZJn/5435sTqS/ncbia5.qbZyiS.db7jUtgtqCS7js/r7mN2YVU.',     'canopy2'),
    ('admin',       '$2b$12$EHRIV4MKmC.CWC6zxN2aCOgLjZsXGvs5BCR4zvA3LFSdirouzhXwa',       'admin');



INSERT INTO drivers (full_name, passport_number, nationality, contact_number, licence_number, licence_expiry) VALUES
    ('Sipho Dlamini', 'A12345678', 'South Africa', '+27821234567', 'C123456789', '2028-03-31'),
    ('Maria Sitoe',   'AB1234567', 'Mozambique',   '+258841234567', 'MZ-55123',  '2027-08-15')
    ;

INSERT INTO trucks (registration_number, country_registration, make_model, year, trailer_registration) VALUES
    ('ND 123-456', 'South Africa', 'Volvo FH 440', 2020, 'ND 654-321'),
    ('AAA-123-MP', 'Mozambique',   'Scania R450',  2019, NULL)
    ;

INSERT INTO crossings (manifest_reference, driver_id, truck_id, crossing_status, lane_id, window_id, processing_minutes, predicted_wait_minutes, arrived_at, allocated_at, immigration_started_at, cleared_at, exited_at) VALUES
    ('MAN-2026-000101', 1, 1, 'exited', 2, 1, 8.5, 6.0,
        DATE_SUB(NOW(), INTERVAL 8640 MINUTE), DATE_SUB(NOW(), INTERVAL 8634 MINUTE),
        DATE_SUB(NOW(), INTERVAL 8620 MINUTE), DATE_SUB(NOW(), INTERVAL 8611 MINUTE),
        DATE_SUB(NOW(), INTERVAL 8598 MINUTE)),
    ('MAN-2026-000140', 2, 2, 'allocated', 3, 2, 6.0, 9.5,
        DATE_SUB(NOW(), INTERVAL 25 MINUTE), DATE_SUB(NOW(), INTERVAL 21 MINUTE),
        NULL, NULL, NULL)
    ;

INSERT INTO crossing_goods (crossing_id, category_id) VALUES (1, 1), (1, 4), (2, 5);

-- Audit trail that we generate from the timestamps above --
INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, NULL, 'registered', arrived_at FROM crossings;

INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, 'registered', 'goods_declared', DATE_ADD(arrived_at, INTERVAL 2 MINUTE)
    FROM crossings WHERE crossing_status <> 'registered';

INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, 'goods_declared', 'allocated', allocated_at FROM crossings WHERE allocated_at IS NOT NULL;

INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, 'allocated', 'at_immigration', immigration_started_at FROM crossings WHERE immigration_started_at IS NOT NULL;
    
INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, 'at_immigration', 'cleared', cleared_at FROM crossings WHERE cleared_at IS NOT NULL;

INSERT INTO status_events (crossing_id, from_status, to_status, created_at)
    SELECT id, 'cleared', 'exited', exited_at FROM crossings WHERE exited_at IS NOT NULL;
