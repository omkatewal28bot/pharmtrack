-- ============================================================
--  PharmTrack Database  —  pharma_db
-- ============================================================
DROP TABLE IF EXISTS transfers;
DROP TABLE IF EXISTS state_distribution;
DROP TABLE IF EXISTS medicines;


-- ── Medicines ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medicines (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(200)   NOT NULL,
    batch_number     VARCHAR(100)   NOT NULL UNIQUE,
    category         VARCHAR(100)   NOT NULL DEFAULT 'Other',
    manufacturer     VARCHAR(200)   NOT NULL DEFAULT '',
    manufacture_date DATE           NOT NULL,
    expiry_date      DATE           NOT NULL,
    quantity         INT            NOT NULL DEFAULT 0,
    unit_price       DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    added_on         DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expiry (expiry_date),
    INDEX idx_category (category)
);

-- ── State Distribution ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS state_distribution (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id    INT          NOT NULL,
    state_name     VARCHAR(100) NOT NULL,
    quantity       INT          NOT NULL,
    distributed_on DATE         NOT NULL,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    INDEX idx_state (state_name)
);

-- ── Transfers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transfers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id     INT          NOT NULL,
    from_state      VARCHAR(100) NOT NULL,
    to_state        VARCHAR(100) NOT NULL,
    quantity        INT          NOT NULL,
    transferred_on  DATE         NOT NULL,
    notes           TEXT,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE,
    INDEX idx_from_state (from_state),
    INDEX idx_to_state   (to_state)
);

-- ── Sample Data ───────────────────────────────────────────────
INSERT INTO medicines (name, batch_number, category, manufacturer, manufacture_date, expiry_date, quantity, unit_price) VALUES
('Paracetamol 500mg',     'PCM-001', 'Analgesic',        'Cipla',           '2023-01-01', '2025-12-31', 500,  5.50),
('Amoxicillin 250mg',     'AMX-002', 'Antibiotic',       'Sun Pharma',      '2023-06-01', '2025-06-01', 200, 18.00),
('Metformin 500mg',       'MET-003', 'Antidiabetic',     'Dr. Reddys',      '2023-03-01', '2026-03-01', 300, 12.00),
('Atorvastatin 10mg',     'ATV-004', 'Cholesterol',      'Lupin',           '2023-09-01', '2026-09-01', 150, 25.00),
('Omeprazole 20mg',       'OMP-005', 'Antacid',          'Torrent',         '2024-01-01', '2026-01-01', 400,  9.00),
('Cetirizine 10mg',       'CTZ-006', 'Antihistamine',    'Mankind',         '2024-02-01', '2026-07-01', 250,  6.00),
('Amlodipine 5mg',        'AML-007', 'Antihypertensive', 'Zydus',           '2023-11-01', '2025-11-01', 180, 15.00),
('Azithromycin 500mg',    'AZT-008', 'Antibiotic',       'Cipla',           '2024-04-01', '2026-04-01', 100, 45.00),
('Pantoprazole 40mg',     'PNT-009', 'Antacid',          'Sun Pharma',      '2024-03-01', '2026-03-15', 320, 11.00),
('Levothyroxine 50mcg',   'LVT-010', 'Thyroid',          'Abbott',          '2023-07-01', '2025-07-01', 220, 30.00),
('Ibuprofen 400mg',       'IBP-011', 'Analgesic',        'Dr. Reddys',      '2024-01-15', '2026-01-15', 600,  7.00),
('Montelukast 10mg',      'MNT-012', 'Respiratory',      'Glenmark',        '2024-05-01', '2026-05-01', 140, 22.00),
('Vitamin D3 60000IU',    'VTD-013', 'Supplement',       'Mankind',         '2024-06-01', '2027-06-01', 500,  8.00),
('Metronidazole 400mg',   'MTR-014', 'Antiparasitic',    'Alkem',           '2023-10-01', '2025-04-01', 180, 10.00),
('Ondansetron 4mg',       'OND-015', 'Antiemetic',       'Wockhardt',       '2024-02-15', '2026-02-15', 220, 14.00);

INSERT INTO state_distribution (medicine_id, state_name, quantity, distributed_on) VALUES
(1,  'Maharashtra',    100, '2024-01-10'),
(2,  'Maharashtra',     50, '2024-01-10'),
(3,  'Gujarat',         80, '2024-02-05'),
(4,  'Gujarat',         40, '2024-02-05'),
(5,  'Karnataka',       90, '2024-03-01'),
(6,  'Karnataka',       60, '2024-03-01'),
(7,  'Tamil Nadu',      70, '2024-03-15'),
(8,  'Tamil Nadu',      30, '2024-03-15'),
(9,  'Rajasthan',       75, '2024-04-01'),
(10, 'Rajasthan',       55, '2024-04-01'),
(11, 'Delhi',          120, '2024-04-10'),
(12, 'Delhi',           35, '2024-04-10'),
(13, 'West Bengal',    100, '2024-05-01'),
(14, 'West Bengal',     45, '2024-05-01'),
(15, 'Uttar Pradesh',   80, '2024-05-15'),
(1,  'Uttar Pradesh',   60, '2024-05-15');

INSERT INTO transfers (medicine_id, from_state, to_state, quantity, transferred_on, notes) VALUES
(1, 'Maharashtra', 'Gujarat',      50, '2024-06-01', 'Surplus stock transfer'),
(2, 'Maharashtra', 'Delhi',        20, '2024-06-05', 'Emergency supply'),
(3, 'Gujarat',     'Rajasthan',    30, '2024-06-10', 'Rebalancing inventory'),
(5, 'Karnataka',   'Tamil Nadu',   40, '2024-06-15', 'Routine redistribution'),
(7, 'Tamil Nadu',  'West Bengal',  25, '2024-06-20', 'Low stock alert'),
(9, 'Rajasthan',   'Uttar Pradesh',35, '2024-07-01', 'Regional request'),
(11,'Delhi',       'Maharashtra',  60, '2024-07-05', 'Surplus transfer'),
(13,'West Bengal', 'Karnataka',    50, '2024-07-10', NULL);