from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import MySQLdb
import MySQLdb.cursors
from datetime import date, datetime
import os

app = Flask(__name__)
app.secret_key = "pharma123"

MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'sql8.freesqldatabase.com')
MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
MYSQL_USER     = os.environ.get('MYSQL_USER', 'sql8822192')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB       = os.environ.get('MYSQL_DB', 'sql8822192')

def get_db():
    return MySQLdb.connect(
        host=MYSQL_HOST,
        port=int(MYSQL_PORT),
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        cursorclass=MySQLdb.cursors.DictCursor,
        ssl={'ssl_mode': 'REQUIRED'}
    )
# ── Domain Knowledge ──────────────────────────────────────────
MEDICINE_INFO = {
    'Analgesic':        {'use': 'Pain relief — headache, fever, body pain', 'icon': '💊', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Avoid direct sunlight'},
    'Antibiotic':       {'use': 'Kills bacteria — infections, pneumonia, UTI', 'icon': '🦠', 'temp': '2-8°C', 'humidity': '<50%', 'light': 'Store in dark place'},
    'Antidiabetic':     {'use': 'Controls blood sugar — Type 2 Diabetes', 'icon': '🩸', 'temp': '15-30°C', 'humidity': '<60%', 'light': 'Keep away from light'},
    'Antihypertensive': {'use': 'Lowers blood pressure — hypertension', 'icon': '❤️', 'temp': '20-25°C', 'humidity': '<55%', 'light': 'Normal indoor light OK'},
    'Antacid':          {'use': 'Reduces stomach acid — acidity, ulcers', 'icon': '🫃', 'temp': '15-30°C', 'humidity': '<65%', 'light': 'Normal light OK'},
    'Antihistamine':    {'use': 'Allergy relief — rashes, sneezing, itching', 'icon': '🤧', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Avoid sunlight'},
    'Cholesterol':      {'use': 'Reduces bad cholesterol — heart disease prevention', 'icon': '🫀', 'temp': '20-25°C', 'humidity': '<60%', 'light': 'Normal light OK'},
    'Antiparasitic':    {'use': 'Kills parasites — malaria, worms, infections', 'icon': '🪱', 'temp': '15-30°C', 'humidity': '<60%', 'light': 'Protect from light'},
    'Antiemetic':       {'use': 'Prevents nausea & vomiting — motion sickness', 'icon': '🤢', 'temp': '15-30°C', 'humidity': '<65%', 'light': 'Normal light OK'},
    'Supplement':       {'use': 'Nutritional support — vitamins, minerals', 'icon': '💪', 'temp': '15-25°C', 'humidity': '<55%', 'light': 'Avoid direct sunlight'},
    'Respiratory':      {'use': 'Breathing support — asthma, allergies, COPD', 'icon': '🫁', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Store in cool place'},
    'Antifungal':       {'use': 'Kills fungal infections — skin, nail, oral', 'icon': '🍄', 'temp': '15-30°C', 'humidity': '<50%', 'light': 'Protect from light'},
    'Neurological':     {'use': 'Brain & nerve support — seizures, depression', 'icon': '🧠', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Avoid light exposure'},
    'Thyroid':          {'use': 'Thyroid hormone regulation — hypothyroidism', 'icon': '🦋', 'temp': '15-30°C', 'humidity': '<65%', 'light': 'Normal light OK'},
    'Eye/Ear':          {'use': 'Eye/ear infections, drops — conjunctivitis', 'icon': '👁️', 'temp': '2-8°C', 'humidity': '<50%', 'light': 'Keep refrigerated'},
    'Skin':             {'use': 'Skin conditions — eczema, psoriasis, acne', 'icon': '🧴', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Avoid direct sunlight'},
    'Cardiac':          {'use': 'Heart conditions — arrhythmia, heart failure', 'icon': '💓', 'temp': '15-25°C', 'humidity': '<55%', 'light': 'Store in dark place'},
    'Other':            {'use': 'General medicine', 'icon': '💊', 'temp': '15-25°C', 'humidity': '<60%', 'light': 'Normal storage'},
}

def get_usability_score(med, temp=25, humidity=60, light_exposure=False):
    """Predict usability based on storage conditions + expiry"""
    category = med.get('category', 'Other')
    info = MEDICINE_INFO.get(category, MEDICINE_INFO['Other'])

    score = 100
    warnings = []

    # Expiry factor
    days = med.get('days', 0)
    if days < 0:
        return 0, ['Medicine is expired — DO NOT USE'], 'expired'
    elif days <= 30:
        score -= 30
        warnings.append(f'Expires in {days} days — use immediately')
    elif days <= 90:
        score -= 10
        warnings.append(f'Expires in {days} days — use soon')

    # Temperature factor
    try:
        temp_range = info['temp'].replace('°C', '').split('-')
        temp_min = int(temp_range[0])
        temp_max = int(temp_range[1])
        if temp < temp_min or temp > temp_max:
            score -= 25
            warnings.append(f'Temperature {temp}°C out of range ({info["temp"]})')
    except:
        pass

    # Humidity factor
    try:
        max_humidity = int(info['humidity'].replace('<', '').replace('%', ''))
        if humidity > max_humidity:
            score -= 20
            warnings.append(f'Humidity {humidity}% too high (max {info["humidity"]})')
    except:
        pass

    # Light factor
    if light_exposure and 'dark' in info['light'].lower():
        score -= 15
        warnings.append('Light exposure detected — store in dark place')
    elif light_exposure and 'sunlight' in info['light'].lower():
        score -= 10
        warnings.append('Avoid direct sunlight exposure')

    score = max(0, score)

    if score >= 80:   grade = 'safe'
    elif score >= 60: grade = 'warning'
    elif score >= 30: grade = 'critical'
    else:             grade = 'expired'

    return score, warnings, grade

def get_status(expiry_date):
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    days = (expiry_date - date.today()).days
    if days < 0:     return days, "expired"
    elif days <= 30: return days, "critical"
    elif days <= 90: return days, "warning"
    else:            return days, "safe"

def enrich(med):
    days, status = get_status(med['expiry_date'])
    med['days']   = days
    med['status'] = status
    if isinstance(med.get('expiry_date'), (date, datetime)):
        med['expiry_date'] = str(med['expiry_date'])
    if isinstance(med.get('manufacture_date'), (date, datetime)):
        med['manufacture_date'] = str(med['manufacture_date'])
    if isinstance(med.get('added_on'), datetime):
        med['added_on'] = str(med['added_on'])
    # Add domain knowledge
    cat = med.get('category', 'Other')
    med['info'] = MEDICINE_INFO.get(cat, MEDICINE_INFO['Other'])
    return med

# ── Index ─────────────────────────────────────────────────────
@app.route('/')
def index():
    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM medicines ORDER BY expiry_date ASC")
    meds = [enrich(m) for m in cur.fetchall()]
    cur.execute("""
        SELECT sd.state_name,
               COUNT(DISTINCT sd.medicine_id) AS medicine_count,
               SUM(sd.quantity) AS total_qty
        FROM state_distribution sd
        GROUP BY sd.state_name
        ORDER BY total_qty DESC LIMIT 8
    """)
    states = cur.fetchall()
    cur.execute("""
        SELECT t.id, m.name AS medicine_name,
               t.from_state, t.to_state, t.quantity, t.transferred_on
        FROM transfers t
        JOIN medicines m ON t.medicine_id = m.id
        ORDER BY t.transferred_on DESC LIMIT 5
    """)
    recent_transfers = cur.fetchall()
    for t in recent_transfers:
        if isinstance(t.get('transferred_on'), (date, datetime)):
            t['transferred_on'] = str(t['transferred_on'])
    cur.close(); db.close()
    stats = {s: sum(1 for m in meds if m['status'] == s)
             for s in ['expired', 'critical', 'warning', 'safe']}
    stats['total'] = len(meds)
    return render_template('index.html', medicines=meds, stats=stats,
                           states=states, transfers=recent_transfers)

# ── Add ───────────────────────────────────────────────────────
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name         = request.form['name'].strip()
        batch        = request.form['batch'].strip()
        cat          = request.form['category']
        manufacturer = request.form['manufacturer'].strip()
        mfg          = request.form['mfg']
        exp          = request.form['exp']
        qty          = request.form['qty']
        price        = request.form.get('price', 0)
        errors = []
        if not name:         errors.append("Medicine name is required.")
        if not batch:        errors.append("Batch number is required.")
        if not manufacturer: errors.append("Manufacturer is required.")
        try:
            mfg_d = datetime.strptime(mfg, "%Y-%m-%d").date()
            exp_d = datetime.strptime(exp, "%Y-%m-%d").date()
            if exp_d <= mfg_d: errors.append("Expiry date must be after manufacture date.")
        except ValueError: errors.append("Invalid date format.")
        try:
            if int(qty) < 0: errors.append("Quantity cannot be negative.")
        except ValueError:   errors.append("Quantity must be a number.")
        if errors:
            for e in errors: flash(e, 'error')
            return render_template('form.html', med=None, action='Add')
        db  = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM medicines WHERE batch_number=%s", (batch,))
        if cur.fetchone():
            flash(f"Batch '{batch}' already exists.", 'error')
            cur.close(); db.close()
            return render_template('form.html', med=None, action='Add')
        cur.execute("""INSERT INTO medicines
                       (name, batch_number, category, manufacturer, manufacture_date, expiry_date, quantity, unit_price)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (name, batch, cat, manufacturer, mfg, exp, qty, price))
        db.commit(); cur.close(); db.close()
        flash('Medicine added!', 'success')
        return redirect(url_for('index'))
    return render_template('form.html', med=None, action='Add')

# ── Edit ──────────────────────────────────────────────────────
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db  = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        name         = request.form['name'].strip()
        batch        = request.form['batch'].strip()
        cat          = request.form['category']
        manufacturer = request.form['manufacturer'].strip()
        mfg          = request.form['mfg']
        exp          = request.form['exp']
        qty          = request.form['qty']
        price        = request.form.get('price', 0)
        errors = []
        try:
            mfg_d = datetime.strptime(mfg, "%Y-%m-%d").date()
            exp_d = datetime.strptime(exp, "%Y-%m-%d").date()
            if exp_d <= mfg_d: errors.append("Expiry date must be after manufacture date.")
        except ValueError: errors.append("Invalid date format.")
        try:
            if int(qty) < 0: errors.append("Quantity cannot be negative.")
        except ValueError:   errors.append("Quantity must be a number.")
        if errors:
            for e in errors: flash(e, 'error')
            cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
            med = enrich(cur.fetchone())
            cur.close(); db.close()
            return render_template('form.html', med=med, action='Edit')
        cur.execute("SELECT id FROM medicines WHERE batch_number=%s AND id!=%s", (batch, id))
        if cur.fetchone():
            flash(f"Batch '{batch}' used by another medicine.", 'error')
            cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
            med = enrich(cur.fetchone())
            cur.close(); db.close()
            return render_template('form.html', med=med, action='Edit')
        cur.execute("""UPDATE medicines SET name=%s,batch_number=%s,category=%s,manufacturer=%s,
                       manufacture_date=%s,expiry_date=%s,quantity=%s,unit_price=%s WHERE id=%s""",
                    (name,batch,cat,manufacturer,mfg,exp,qty,price,id))
        db.commit(); cur.close(); db.close()
        flash('Medicine updated!', 'success')
        return redirect(url_for('index'))
    cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    row = cur.fetchone()
    cur.close(); db.close()
    if not row:
        flash('Medicine not found.', 'error')
        return redirect(url_for('index'))
    return render_template('form.html', med=enrich(row), action='Edit')

# ── Delete ────────────────────────────────────────────────────
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit(); cur.close(); db.close()
    flash('Medicine deleted.', 'info')
    return redirect(url_for('index'))

# ── States ────────────────────────────────────────────────────
@app.route('/states')
def states():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT sd.state_name, m.name AS medicine_name, m.category,
               sd.quantity, sd.distributed_on, m.expiry_date
        FROM state_distribution sd
        JOIN medicines m ON sd.medicine_id = m.id
        ORDER BY sd.state_name, sd.distributed_on DESC
    """)
    rows = cur.fetchall()
    cur.close(); db.close()
    state_map = {}
    for row in rows:
        if isinstance(row.get('expiry_date'), (date, datetime)):
            row['expiry_date'] = str(row['expiry_date'])
        if isinstance(row.get('distributed_on'), (date, datetime)):
            row['distributed_on'] = str(row['distributed_on'])
        _, row['status'] = get_status(row['expiry_date'])
        state_map.setdefault(row['state_name'], []).append(row)
    return render_template('states.html', state_map=state_map)

# ── Distribute ────────────────────────────────────────────────
@app.route('/distribute', methods=['GET', 'POST'])
def distribute():
    db  = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        medicine_id = request.form['medicine_id']
        state_name  = request.form['state_name'].strip()
        quantity    = request.form['quantity']
        dist_date   = request.form['distributed_on']
        errors = []
        if not state_name: errors.append("State name is required.")
        try:
            if int(quantity) <= 0: errors.append("Quantity must be positive.")
        except ValueError: errors.append("Quantity must be a number.")
        cur.execute("SELECT quantity FROM medicines WHERE id=%s", (medicine_id,))
        med = cur.fetchone()
        if med and int(quantity) > med['quantity']:
            errors.append(f"Only {med['quantity']} units available.")
        if errors:
            for e in errors: flash(e, 'error')
        else:
            cur.execute("""INSERT INTO state_distribution (medicine_id,state_name,quantity,distributed_on)
                           VALUES (%s,%s,%s,%s)""", (medicine_id,state_name,quantity,dist_date))
            cur.execute("UPDATE medicines SET quantity=quantity-%s WHERE id=%s", (quantity,medicine_id))
            db.commit()
            flash('Distribution recorded!', 'success')
            cur.close(); db.close()
            return redirect(url_for('states'))
    cur.execute("SELECT id, name, batch_number, quantity FROM medicines ORDER BY name")
    meds = cur.fetchall()
    cur.close(); db.close()
    return render_template('distribute.html', medicines=meds, today=str(date.today()))

# ── Transfers ─────────────────────────────────────────────────
@app.route('/transfers')
def transfers():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT t.id, m.name AS medicine_name, m.category,
               t.from_state, t.to_state, t.quantity, t.transferred_on, t.notes
        FROM transfers t
        JOIN medicines m ON t.medicine_id = m.id
        ORDER BY t.transferred_on DESC
    """)
    rows = cur.fetchall()
    cur.close(); db.close()
    for t in rows:
        if isinstance(t.get('transferred_on'), (date, datetime)):
            t['transferred_on'] = str(t['transferred_on'])
    return render_template('transfers.html', transfers=rows)

# ── Add Transfer ──────────────────────────────────────────────
@app.route('/transfer/add', methods=['GET', 'POST'])
def add_transfer():
    db  = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        medicine_id   = request.form['medicine_id']
        from_state    = request.form['from_state'].strip()
        to_state      = request.form['to_state'].strip()
        quantity      = request.form['quantity']
        transfer_date = request.form['transferred_on']
        notes         = request.form.get('notes', '').strip()
        errors = []
        if not from_state: errors.append("From state is required.")
        if not to_state:   errors.append("To state is required.")
        if from_state == to_state: errors.append("From and To cannot be same.")
        try:
            if int(quantity) <= 0: errors.append("Quantity must be positive.")
        except ValueError: errors.append("Quantity must be a number.")
        if errors:
            for e in errors: flash(e, 'error')
        else:
            cur.execute("""INSERT INTO transfers (medicine_id,from_state,to_state,quantity,transferred_on,notes)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (medicine_id,from_state,to_state,quantity,transfer_date,notes))
            db.commit()
            flash('Transfer recorded!', 'success')
            cur.close(); db.close()
            return redirect(url_for('transfers'))
    cur.execute("SELECT id, name, batch_number FROM medicines ORDER BY name")
    meds = cur.fetchall()
    cur.close(); db.close()
    return render_template('add_transfer.html', medicines=meds, today=str(date.today()))

# ── FEATURE 1: Usability Predictor ───────────────────────────
@app.route('/usability', methods=['GET', 'POST'])
def usability():
    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM medicines ORDER BY name")
    medicines = [enrich(m) for m in cur.fetchall()]
    cur.close(); db.close()

    results = []
    temp     = 25
    humidity = 60
    light    = False

    if request.method == 'POST':
        temp     = float(request.form.get('temperature', 25))
        humidity = float(request.form.get('humidity', 60))
        light    = request.form.get('light_exposure') == 'yes'
        for med in medicines:
            score, warnings, grade = get_usability_score(med, temp, humidity, light)
            results.append({**med, 'score': score, 'warnings': warnings, 'grade': grade})
        results.sort(key=lambda x: x['score'])
    else:
        for med in medicines:
            score, warnings, grade = get_usability_score(med, temp, humidity, light)
            results.append({**med, 'score': score, 'warnings': warnings, 'grade': grade})

    return render_template('usability.html', results=results,
                           temp=temp, humidity=humidity, light=light)

# ── FEATURE 2: Demand + Expiry Prediction ────────────────────
@app.route('/prediction')
def prediction():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT m.id, m.name, m.category, m.quantity, m.expiry_date,
               m.unit_price, m.batch_number,
               COALESCE(SUM(sd.quantity), 0) AS total_distributed
        FROM medicines m
        LEFT JOIN state_distribution sd ON m.id = sd.medicine_id
        GROUP BY m.id
        ORDER BY m.expiry_date ASC
    """)
    rows = cur.fetchall()
    cur.close(); db.close()

    predictions = []
    for row in rows:
        days, status = get_status(row['expiry_date'])
        if isinstance(row['expiry_date'], (date, datetime)):
            row['expiry_date'] = str(row['expiry_date'])

        distributed = row['total_distributed'] or 0
        stock       = row['quantity'] or 0

        # Demand score — how fast is it moving
        if distributed == 0:
            demand = 'Low'
            demand_score = 1
        elif distributed < 50:
            demand = 'Medium'
            demand_score = 2
        else:
            demand = 'High'
            demand_score = 3

        # Days to sell at current rate
        if distributed > 0 and stock > 0:
            daily_rate   = distributed / 180  # approx 6 months data
            days_to_sell = int(stock / daily_rate) if daily_rate > 0 else 999
        else:
            days_to_sell = 999

        # Risk: will it expire before being sold?
        if days < 0:
            risk = 'Expired'
            risk_color = 'expired'
        elif days_to_sell > days and days > 0:
            risk = 'Will Expire Before Sale!'
            risk_color = 'critical'
        elif days <= 90:
            risk = 'Sell Soon'
            risk_color = 'warning'
        else:
            risk = 'On Track'
            risk_color = 'safe'

        predictions.append({
            **row,
            'days': days,
            'status': status,
            'demand': demand,
            'demand_score': demand_score,
            'days_to_sell': days_to_sell if days_to_sell != 999 else 'N/A',
            'distributed': distributed,
            'risk': risk,
            'risk_color': risk_color,
            'info': MEDICINE_INFO.get(row['category'], MEDICINE_INFO['Other'])
        })

    return render_template('prediction.html', predictions=predictions)

# ── FEATURE 3: Domain Knowledge ──────────────────────────────
@app.route('/knowledge')
def knowledge():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT category, COUNT(*) as count, SUM(quantity) as total_qty
        FROM medicines GROUP BY category
    """)
    cat_stats = {r['category']: r for r in cur.fetchall()}
    cur.close(); db.close()
    return render_template('knowledge.html',
                           medicine_info=MEDICINE_INFO,
                           cat_stats=cat_stats)

# ── FEATURE 4: FIFO Batch Analysis ───────────────────────────
@app.route('/fifo')
def fifo():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, name, batch_number, category, manufacturer,
               manufacture_date, expiry_date, quantity, unit_price
        FROM medicines
        WHERE quantity > 0
        ORDER BY name, expiry_date ASC
    """)
    rows = cur.fetchall()
    cur.close(); db.close()

    # Group by medicine name for FIFO
    batches = {}
    for row in rows:
        days, status = get_status(row['expiry_date'])
        if isinstance(row['expiry_date'], (date, datetime)):
            row['expiry_date'] = str(row['expiry_date'])
        if isinstance(row['manufacture_date'], (date, datetime)):
            row['manufacture_date'] = str(row['manufacture_date'])
        row['days']   = days
        row['status'] = status

        name = row['name'].split(' ')[0]  # group by base name
        if name not in batches:
            batches[name] = []
        batches[name].append(row)

    # Mark FIFO order
    fifo_list = []
    for name, batch_group in batches.items():
        for i, b in enumerate(sorted(batch_group, key=lambda x: x['expiry_date'])):
            b['fifo_order'] = i + 1
            b['sell_first'] = (i == 0)
            fifo_list.append(b)

    fifo_list.sort(key=lambda x: x['expiry_date'])
    return render_template('fifo.html', batches=batches, fifo_list=fifo_list)

# ── API ───────────────────────────────────────────────────────
@app.route('/api')
def api():
    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM medicines ORDER BY expiry_date ASC")
    meds = [enrich(m) for m in cur.fetchall()]
    cur.close(); db.close()
    return jsonify(meds)

if __name__ == '__main__':
    app.run(debug=True)