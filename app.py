from flask import Flask, request, jsonify
from flask_cors import CORS
import MySQLdb
import MySQLdb.cursors
from datetime import date, datetime
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# DATABASE CONFIGURATION
# Set these in Render Environment Variables
# ============================================================

MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")


def get_db():
    if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
        raise RuntimeError(
            "Database environment variables are missing. "
            "Set MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
            "MYSQL_PASSWORD and MYSQL_DB in Render."
        )

    return MySQLdb.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        cursorclass=MySQLdb.cursors.DictCursor
    )


# ============================================================
# DOMAIN KNOWLEDGE
# ============================================================

MEDICINE_INFO = {
    "Analgesic": {
        "use": "Pain relief — headache, fever, body pain",
        "icon": "💊",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Avoid direct sunlight"
    },
    "Antibiotic": {
        "use": "Kills bacteria — infections, pneumonia, UTI",
        "icon": "🦠",
        "temp": "2-8°C",
        "humidity": "<50%",
        "light": "Store in dark place"
    },
    "Antidiabetic": {
        "use": "Controls blood sugar — Type 2 Diabetes",
        "icon": "🩸",
        "temp": "15-30°C",
        "humidity": "<60%",
        "light": "Keep away from light"
    },
    "Antihypertensive": {
        "use": "Lowers blood pressure — hypertension",
        "icon": "❤️",
        "temp": "20-25°C",
        "humidity": "<55%",
        "light": "Normal indoor light OK"
    },
    "Antacid": {
        "use": "Reduces stomach acid — acidity, ulcers",
        "icon": "🫃",
        "temp": "15-30°C",
        "humidity": "<65%",
        "light": "Normal light OK"
    },
    "Antihistamine": {
        "use": "Allergy relief — rashes, sneezing, itching",
        "icon": "🤧",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Avoid sunlight"
    },
    "Cholesterol": {
        "use": "Reduces bad cholesterol — heart disease prevention",
        "icon": "🫀",
        "temp": "20-25°C",
        "humidity": "<60%",
        "light": "Normal light OK"
    },
    "Antiparasitic": {
        "use": "Kills parasites — malaria, worms, infections",
        "icon": "🪱",
        "temp": "15-30°C",
        "humidity": "<60%",
        "light": "Protect from light"
    },
    "Antiemetic": {
        "use": "Prevents nausea & vomiting — motion sickness",
        "icon": "🤢",
        "temp": "15-30°C",
        "humidity": "<65%",
        "light": "Normal light OK"
    },
    "Supplement": {
        "use": "Nutritional support — vitamins, minerals",
        "icon": "💪",
        "temp": "15-25°C",
        "humidity": "<55%",
        "light": "Avoid direct sunlight"
    },
    "Respiratory": {
        "use": "Breathing support — asthma, allergies, COPD",
        "icon": "🫁",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Store in cool place"
    },
    "Antifungal": {
        "use": "Kills fungal infections — skin, nail, oral",
        "icon": "🍄",
        "temp": "15-30°C",
        "humidity": "<50%",
        "light": "Protect from light"
    },
    "Neurological": {
        "use": "Brain & nerve support — seizures, depression",
        "icon": "🧠",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Avoid light exposure"
    },
    "Thyroid": {
        "use": "Thyroid hormone regulation — hypothyroidism",
        "icon": "🦋",
        "temp": "15-30°C",
        "humidity": "<65%",
        "light": "Normal light OK"
    },
    "Eye/Ear": {
        "use": "Eye/ear infections, drops — conjunctivitis",
        "icon": "👁️",
        "temp": "2-8°C",
        "humidity": "<50%",
        "light": "Keep refrigerated"
    },
    "Skin": {
        "use": "Skin conditions — eczema, psoriasis, acne",
        "icon": "🧴",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Avoid direct sunlight"
    },
    "Cardiac": {
        "use": "Heart conditions — arrhythmia, heart failure",
        "icon": "💓",
        "temp": "15-25°C",
        "humidity": "<55%",
        "light": "Store in dark place"
    },
    "Other": {
        "use": "General medicine",
        "icon": "💊",
        "temp": "15-25°C",
        "humidity": "<60%",
        "light": "Normal storage"
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_status(expiry_date):

    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(
            expiry_date, "%Y-%m-%d"
        ).date()

    days = (expiry_date - date.today()).days

    if days < 0:
        return days, "expired"
    elif days <= 30:
        return days, "critical"
    elif days <= 90:
        return days, "warning"
    else:
        return days, "safe"


def serialize(value):

    if isinstance(value, (date, datetime)):
        return str(value)

    return value


def enrich(med):

    med = dict(med)

    days, status = get_status(med["expiry_date"])

    med["days"] = days
    med["status"] = status

    for key in [
        "expiry_date",
        "manufacture_date",
        "added_on"
    ]:
        if key in med:
            med[key] = serialize(med[key])

    category = med.get("category", "Other")

    med["info"] = MEDICINE_INFO.get(
        category,
        MEDICINE_INFO["Other"]
    )

    return med


def get_usability_score(
    med,
    temp=25,
    humidity=60,
    light_exposure=False
):

    category = med.get("category", "Other")

    info = MEDICINE_INFO.get(
        category,
        MEDICINE_INFO["Other"]
    )

    score = 100
    warnings = []

    days = med.get("days", 0)

    if days < 0:

        return (
            0,
            ["Medicine is expired — DO NOT USE"],
            "expired"
        )

    elif days <= 30:

        score -= 30
        warnings.append(
            f"Expires in {days} days — use immediately"
        )

    elif days <= 90:

        score -= 10
        warnings.append(
            f"Expires in {days} days — use soon"
        )

    try:

        temp_range = (
            info["temp"]
            .replace("°C", "")
            .split("-")
        )

        temp_min = int(temp_range[0])
        temp_max = int(temp_range[1])

        if temp < temp_min or temp > temp_max:

            score -= 25

            warnings.append(
                f"Temperature {temp}°C out of range "
                f"({info['temp']})"
            )

    except Exception:
        pass

    try:

        max_humidity = int(
            info["humidity"]
            .replace("<", "")
            .replace("%", "")
        )

        if humidity > max_humidity:

            score -= 20

            warnings.append(
                f"Humidity {humidity}% too high "
                f"(max {info['humidity']})"
            )

    except Exception:
        pass

    if light_exposure:

        if "dark" in info["light"].lower():

            score -= 15

            warnings.append(
                "Light exposure detected — "
                "store in dark place"
            )

        elif "sunlight" in info["light"].lower():

            score -= 10

            warnings.append(
                "Avoid direct sunlight exposure"
            )

    score = max(0, score)

    if score >= 80:
        grade = "safe"
    elif score >= 60:
        grade = "warning"
    elif score >= 30:
        grade = "critical"
    else:
        grade = "expired"

    return score, warnings, grade


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "PharmTrack API is running",
        "frontend": "Netlify",
        "backend": "Render"
    })


@app.route("/api/health")
def health():

    try:

        db = get_db()
        db.close()

        return jsonify({
            "success": True,
            "database": "connected"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "database": "error",
            "message": str(e)
        }), 500


# ============================================================
# MEDICINES - GET
# ============================================================

@app.route("/api/medicines", methods=["GET"])
def get_medicines():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM medicines "
            "ORDER BY expiry_date ASC"
        )

        medicines = [
            enrich(m)
            for m in cur.fetchall()
        ]

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "medicines": medicines
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# MEDICINE - GET SINGLE
# ============================================================

@app.route("/api/medicines/<int:id>", methods=["GET"])
def get_medicine(id):

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM medicines WHERE id=%s",
            (id,)
        )

        medicine = cur.fetchone()

        cur.close()
        db.close()

        if not medicine:

            return jsonify({
                "success": False,
                "message": "Medicine not found"
            }), 404

        return jsonify({
            "success": True,
            "medicine": enrich(medicine)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# MEDICINE - ADD
# ============================================================

@app.route("/api/medicines", methods=["POST"])
def add_medicine():

    try:

        data = request.get_json()

        required = [
            "name",
            "batch_number",
            "category",
            "manufacturer",
            "manufacture_date",
            "expiry_date",
            "quantity"
        ]

        for field in required:

            if field not in data:

                return jsonify({
                    "success": False,
                    "message": f"{field} is required"
                }), 400

        name = data["name"].strip()
        batch = data["batch_number"].strip()
        category = data["category"]
        manufacturer = data["manufacturer"].strip()
        mfg = data["manufacture_date"]
        exp = data["expiry_date"]
        quantity = int(data["quantity"])
        price = data.get("unit_price", 0)

        if quantity < 0:

            return jsonify({
                "success": False,
                "message": "Quantity cannot be negative"
            }), 400

        mfg_date = datetime.strptime(
            mfg, "%Y-%m-%d"
        ).date()

        exp_date = datetime.strptime(
            exp, "%Y-%m-%d"
        ).date()

        if exp_date <= mfg_date:

            return jsonify({
                "success": False,
                "message": "Expiry date must be after manufacture date"
            }), 400

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT id FROM medicines "
            "WHERE batch_number=%s",
            (batch,)
        )

        if cur.fetchone():

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Batch number already exists"
            }), 409

        cur.execute(
            """
            INSERT INTO medicines
            (
                name,
                batch_number,
                category,
                manufacturer,
                manufacture_date,
                expiry_date,
                quantity,
                unit_price
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                name,
                batch,
                category,
                manufacturer,
                mfg,
                exp,
                quantity,
                price
            )
        )

        db.commit()

        new_id = cur.lastrowid

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Medicine added successfully",
            "id": new_id
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# MEDICINE - UPDATE
# ============================================================

@app.route("/api/medicines/<int:id>", methods=["PUT"])
def update_medicine(id):

    try:

        data = request.get_json()

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT id FROM medicines WHERE id=%s",
            (id,)
        )

        if not cur.fetchone():

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Medicine not found"
            }), 404

        name = data["name"].strip()
        batch = data["batch_number"].strip()
        category = data["category"]
        manufacturer = data["manufacturer"].strip()
        mfg = data["manufacture_date"]
        exp = data["expiry_date"]
        quantity = int(data["quantity"])
        price = data.get("unit_price", 0)

        mfg_date = datetime.strptime(
            mfg, "%Y-%m-%d"
        ).date()

        exp_date = datetime.strptime(
            exp, "%Y-%m-%d"
        ).date()

        if exp_date <= mfg_date:

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Expiry date must be after manufacture date"
            }), 400

        cur.execute(
            """
            SELECT id FROM medicines
            WHERE batch_number=%s AND id!=%s
            """,
            (batch, id)
        )

        if cur.fetchone():

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Batch number already exists"
            }), 409

        cur.execute(
            """
            UPDATE medicines
            SET
                name=%s,
                batch_number=%s,
                category=%s,
                manufacturer=%s,
                manufacture_date=%s,
                expiry_date=%s,
                quantity=%s,
                unit_price=%s
            WHERE id=%s
            """,
            (
                name,
                batch,
                category,
                manufacturer,
                mfg,
                exp,
                quantity,
                price,
                id
            )
        )

        db.commit()

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Medicine updated successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# MEDICINE - DELETE
# ============================================================

@app.route("/api/medicines/<int:id>", methods=["DELETE"])
def delete_medicine(id):

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "DELETE FROM medicines WHERE id=%s",
            (id,)
        )

        if cur.rowcount == 0:

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Medicine not found"
            }), 404

        db.commit()

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Medicine deleted successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# DASHBOARD STATS
# ============================================================

@app.route("/api/dashboard", methods=["GET"])
def dashboard():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM medicines "
            "ORDER BY expiry_date ASC"
        )

        medicines = [
            enrich(m)
            for m in cur.fetchall()
        ]

        stats = {
            "total": len(medicines),
            "expired": sum(
                m["status"] == "expired"
                for m in medicines
            ),
            "critical": sum(
                m["status"] == "critical"
                for m in medicines
            ),
            "warning": sum(
                m["status"] == "warning"
                for m in medicines
            ),
            "safe": sum(
                m["status"] == "safe"
                for m in medicines
            )
        }

        cur.execute(
            """
            SELECT
                sd.state_name,
                COUNT(DISTINCT sd.medicine_id)
                    AS medicine_count,
                SUM(sd.quantity)
                    AS total_qty
            FROM state_distribution sd
            GROUP BY sd.state_name
            ORDER BY total_qty DESC
            LIMIT 8
            """
        )

        states = cur.fetchall()

        cur.execute(
            """
            SELECT
                t.id,
                m.name AS medicine_name,
                t.from_state,
                t.to_state,
                t.quantity,
                t.transferred_on
            FROM transfers t
            JOIN medicines m
                ON t.medicine_id = m.id
            ORDER BY t.transferred_on DESC
            LIMIT 5
            """
        )

        transfers = cur.fetchall()

        for t in transfers:

            if isinstance(
                t.get("transferred_on"),
                (date, datetime)
            ):

                t["transferred_on"] = str(
                    t["transferred_on"]
                )

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "stats": stats,
            "medicines": medicines,
            "states": states,
            "transfers": transfers
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# STATES
# ============================================================

@app.route("/api/states", methods=["GET"])
def get_states():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                sd.state_name,
                m.name AS medicine_name,
                m.category,
                sd.quantity,
                sd.distributed_on,
                m.expiry_date
            FROM state_distribution sd
            JOIN medicines m
                ON sd.medicine_id = m.id
            ORDER BY
                sd.state_name,
                sd.distributed_on DESC
            """
        )

        rows = cur.fetchall()

        cur.close()
        db.close()

        for row in rows:

            row["expiry_date"] = serialize(
                row["expiry_date"]
            )

            row["distributed_on"] = serialize(
                row["distributed_on"]
            )

            _, row["status"] = get_status(
                row["expiry_date"]
            )

        return jsonify({
            "success": True,
            "states": rows
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# DISTRIBUTION
# ============================================================

@app.route("/api/distribute", methods=["POST"])
def distribute():

    try:

        data = request.get_json()

        medicine_id = data["medicine_id"]
        state_name = data["state_name"].strip()
        quantity = int(data["quantity"])
        distributed_on = data.get(
            "distributed_on",
            str(date.today())
        )

        if not state_name:

            return jsonify({
                "success": False,
                "message": "State name is required"
            }), 400

        if quantity <= 0:

            return jsonify({
                "success": False,
                "message": "Quantity must be positive"
            }), 400

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT quantity FROM medicines "
            "WHERE id=%s",
            (medicine_id,)
        )

        med = cur.fetchone()

        if not med:

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Medicine not found"
            }), 404

        if quantity > med["quantity"]:

            cur.close()
            db.close()

            return jsonify({
                "success": False,
                "message":
                    f"Only {med['quantity']} units available"
            }), 400

        cur.execute(
            """
            INSERT INTO state_distribution
            (
                medicine_id,
                state_name,
                quantity,
                distributed_on
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                medicine_id,
                state_name,
                quantity,
                distributed_on
            )
        )

        cur.execute(
            """
            UPDATE medicines
            SET quantity = quantity - %s
            WHERE id=%s
            """,
            (quantity, medicine_id)
        )

        db.commit()

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Distribution recorded"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# TRANSFERS
# ============================================================

@app.route("/api/transfers", methods=["GET"])
def get_transfers():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                t.id,
                m.name AS medicine_name,
                m.category,
                t.from_state,
                t.to_state,
                t.quantity,
                t.transferred_on,
                t.notes
            FROM transfers t
            JOIN medicines m
                ON t.medicine_id = m.id
            ORDER BY t.transferred_on DESC
            """
        )

        rows = cur.fetchall()

        cur.close()
        db.close()

        for row in rows:

            row["transferred_on"] = serialize(
                row["transferred_on"]
            )

        return jsonify({
            "success": True,
            "transfers": rows
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/transfers", methods=["POST"])
def add_transfer_api():

    try:

        data = request.get_json()

        medicine_id = data["medicine_id"]
        from_state = data["from_state"].strip()
        to_state = data["to_state"].strip()
        quantity = int(data["quantity"])
        transferred_on = data.get(
            "transferred_on",
            str(date.today())
        )
        notes = data.get("notes", "").strip()

        if not from_state or not to_state:

            return jsonify({
                "success": False,
                "message":
                    "From state and To state are required"
            }), 400

        if from_state == to_state:

            return jsonify({
                "success": False,
                "message":
                    "From and To states cannot be same"
            }), 400

        if quantity <= 0:

            return jsonify({
                "success": False,
                "message":
                    "Quantity must be positive"
            }), 400

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            INSERT INTO transfers
            (
                medicine_id,
                from_state,
                to_state,
                quantity,
                transferred_on,
                notes
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                medicine_id,
                from_state,
                to_state,
                quantity,
                transferred_on,
                notes
            )
        )

        db.commit()

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Transfer recorded"
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# USABILITY
# ============================================================

@app.route("/api/usability", methods=["POST"])
def usability_api():

    try:

        data = request.get_json() or {}

        temp = float(
            data.get("temperature", 25)
        )

        humidity = float(
            data.get("humidity", 60)
        )

        light = data.get(
            "light_exposure",
            False
        )

        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM medicines "
            "ORDER BY name"
        )

        medicines = [
            enrich(m)
            for m in cur.fetchall()
        ]

        cur.close()
        db.close()

        results = []

        for med in medicines:

            score, warnings, grade = \
                get_usability_score(
                    med,
                    temp,
                    humidity,
                    light
                )

            results.append({
                **med,
                "score": score,
                "warnings": warnings,
                "grade": grade
            })

        results.sort(
            key=lambda x: x["score"]
        )

        return jsonify({
            "success": True,
            "temperature": temp,
            "humidity": humidity,
            "light_exposure": light,
            "results": results
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# PREDICTION
# ============================================================

@app.route("/api/prediction", methods=["GET"])
def prediction_api():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                m.id,
                m.name,
                m.category,
                m.quantity,
                m.expiry_date,
                m.unit_price,
                m.batch_number,
                COALESCE(
                    SUM(sd.quantity), 0
                ) AS total_distributed
            FROM medicines m
            LEFT JOIN state_distribution sd
                ON m.id = sd.medicine_id
            GROUP BY m.id
            ORDER BY m.expiry_date ASC
            """
        )

        rows = cur.fetchall()

        cur.close()
        db.close()

        predictions = []

        for row in rows:

            days, status = get_status(
                row["expiry_date"]
            )

            row["expiry_date"] = serialize(
                row["expiry_date"]
            )

            distributed = (
                row["total_distributed"] or 0
            )

            stock = row["quantity"] or 0

            if distributed == 0:

                demand = "Low"
                demand_score = 1

            elif distributed < 50:

                demand = "Medium"
                demand_score = 2

            else:

                demand = "High"
                demand_score = 3

            if distributed > 0 and stock > 0:

                daily_rate = distributed / 180

                days_to_sell = int(
                    stock / daily_rate
                )

            else:

                days_to_sell = 999

            if days < 0:

                risk = "Expired"
                risk_color = "expired"

            elif days_to_sell > days and days > 0:

                risk = "Will Expire Before Sale!"
                risk_color = "critical"

            elif days <= 90:

                risk = "Sell Soon"
                risk_color = "warning"

            else:

                risk = "On Track"
                risk_color = "safe"

            predictions.append({
                **row,
                "days": days,
                "status": status,
                "demand": demand,
                "demand_score": demand_score,
                "days_to_sell":
                    days_to_sell
                    if days_to_sell != 999
                    else "N/A",
                "distributed": distributed,
                "risk": risk,
                "risk_color": risk_color,
                "info": MEDICINE_INFO.get(
                    row["category"],
                    MEDICINE_INFO["Other"]
                )
            })

        return jsonify({
            "success": True,
            "predictions": predictions
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# KNOWLEDGE
# ============================================================

@app.route("/api/knowledge", methods=["GET"])
def knowledge_api():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                category,
                COUNT(*) AS count,
                SUM(quantity) AS total_qty
            FROM medicines
            GROUP BY category
            """
        )

        category_stats = cur.fetchall()

        cur.close()
        db.close()

        return jsonify({
            "success": True,
            "medicine_info": MEDICINE_INFO,
            "category_stats": category_stats
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# FIFO
# ============================================================

@app.route("/api/fifo", methods=["GET"])
def fifo_api():

    try:

        db = get_db()
        cur = db.cursor()

        cur.execute(
            """
            SELECT
                id,
                name,
                batch_number,
                category,
                manufacturer,
                manufacture_date,
                expiry_date,
                quantity,
                unit_price
            FROM medicines
            WHERE quantity > 0
            ORDER BY name, expiry_date ASC
            """
        )

        rows = cur.fetchall()

        cur.close()
        db.close()

        batches = {}

        for row in rows:

            days, status = get_status(
                row["expiry_date"]
            )

            row["expiry_date"] = serialize(
                row["expiry_date"]
            )

            row["manufacture_date"] = serialize(
                row["manufacture_date"]
            )

            row["days"] = days
            row["status"] = status

            name = row["name"].split(" ")[0]

            batches.setdefault(
                name, []
            ).append(row)

        fifo_list = []

        for name, batch_group in batches.items():

            sorted_batches = sorted(
                batch_group,
                key=lambda x: x["expiry_date"]
            )

            for i, batch in enumerate(
                sorted_batches
            ):

                batch["fifo_order"] = i + 1
                batch["sell_first"] = i == 0

                fifo_list.append(batch)

        fifo_list.sort(
            key=lambda x: x["expiry_date"]
        )

        return jsonify({
            "success": True,
            "batches": batches,
            "fifo_list": fifo_list
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# OLD API COMPATIBILITY
# ============================================================

@app.route("/api", methods=["GET"])
def old_api():

    return get_medicines()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )