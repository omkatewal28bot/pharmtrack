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
        port=MYSQL_PORT,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        cursorclass=MySQLdb.cursors.DictCursor
    )

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
    return med

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
            flash(f"Batch number '{batch}' already exists.", 'error')
            cur.close(); db.close()
            return render_template('form.html', med=None, action='Add')
        cur.execute("""INSERT INTO medicines
                       (name, batch_number, category, manufacturer, manufacture_date, expiry_date, quantity, unit_price)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (name, batch, cat, manufacturer, mfg, exp, qty, price))
        db.commit()
        cur.close(); db.close()
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('form.html', med=None, action='Add')

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
        cur.execute("SELECT id FROM medicines WHERE batch_number=%s AND id != %s", (batch, id))
        if cur.fetchone():
            flash(f"Batch number '{batch}' is used by another medicine.", 'error')
            cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
            med = enrich(cur.fetchone())
            cur.close(); db.close()
            return render_template('form.html', med=med, action='Edit')
        cur.execute("""UPDATE medicines
                       SET name=%s, batch_number=%s, category=%s, manufacturer=%s,
                           manufacture_date=%s, expiry_date=%s, quantity=%s, unit_price=%s
                       WHERE id=%s""",
                    (name, batch, cat, manufacturer, mfg, exp, qty, price, id))
        db.commit()
        cur.close(); db.close()
        flash('Medicine updated successfully!', 'success')
        return redirect(url_for('index'))
    cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    row = cur.fetchone()
    cur.close(); db.close()
    if not row:
        flash('Medicine not found.', 'error')
        return redirect(url_for('index'))
    return render_template('form.html', med=enrich(row), action='Edit')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM medicines WHERE id=%s", (id,))
    db.commit()
    cur.close(); db.close()
    flash('Medicine deleted.', 'info')
    return redirect(url_for('index'))

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
            cur.execute("""INSERT INTO state_distribution (medicine_id, state_name, quantity, distributed_on)
                           VALUES (%s, %s, %s, %s)""", (medicine_id, state_name, quantity, dist_date))
            cur.execute("UPDATE medicines SET quantity = quantity - %s WHERE id=%s", (quantity, medicine_id))
            db.commit()
            flash('Distribution recorded!', 'success')
            cur.close(); db.close()
            return redirect(url_for('states'))
    cur.execute("SELECT id, name, batch_number, quantity FROM medicines ORDER BY name")
    meds = cur.fetchall()
    cur.close(); db.close()
    return render_template('distribute.html', medicines=meds, today=str(date.today()))

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
        if from_state == to_state: errors.append("From and To states cannot be the same.")
        try:
            if int(quantity) <= 0: errors.append("Quantity must be positive.")
        except ValueError: errors.append("Quantity must be a number.")
        if errors:
            for e in errors: flash(e, 'error')
        else:
            cur.execute("""INSERT INTO transfers (medicine_id, from_state, to_state, quantity, transferred_on, notes)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (medicine_id, from_state, to_state, quantity, transfer_date, notes))
            db.commit()
            flash('Transfer recorded!', 'success')
            cur.close(); db.close()
            return redirect(url_for('transfers'))
    cur.execute("SELECT id, name, batch_number FROM medicines ORDER BY name")
    meds = cur.fetchall()
    cur.close(); db.close()
    return render_template('add_transfer.html', medicines=meds, today=str(date.today()))

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