from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import date, datetime
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# MONGODB CONFIGURATION
# Set MONGODB_URI in Render Environment Variables
# ============================================================

MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB = os.environ.get("MONGODB_DB", "pharmtrack")

client = None
db = None


def get_db():
    global client, db

    if not MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI environment variable is missing. "
            "Add your MongoDB Atlas connection string in Render."
        )

    if client is None:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]

    return db


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
# HELPERS
# ============================================================

def get_status(expiry_date):

    if isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()

    elif isinstance(expiry_date, str):
        expiry_date = datetime.strptime(
            expiry_date[:10],
            "%Y-%m-%d"
        ).date()

    days = (expiry_date - date.today()).days

    if days < 0:
        return days, "expired"

    elif days <= 30:
        return days, "critical"

    elif days <= 90:
        return days, "warning"

    return days, "safe"


def serialize(value):

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def clean_document(doc):

    if not doc:
        return None

    doc = dict(doc)

    doc.pop("_id", None)

    return doc


def enrich(med):

    med = clean_document(med)

    days, status = get_status(
        med["expiry_date"]
    )

    med["days"] = days
    med["status"] = status

    for key in [
        "expiry_date",
        "manufacture_date",
        "added_on"
    ]:
        if key in med:
            med[key] = serialize(med[key])

    category = med.get(
        "category",
        "Other"
    )

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

    category = med.get(
        "category",
        "Other"
    )

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
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "PharmTrack API is running",
        "frontend": "Netlify",
        "backend": "Render",
        "database": "MongoDB Atlas"
    })


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health")
def health():

    try:

        database = get_db()

        database.command("ping")

        return jsonify({
            "success": True,
            "database": "connected",
            "database_type": "MongoDB Atlas"
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

        database = get_db()

        rows = database.medicines.find(
            {}
        ).sort(
            "expiry_date",
            1
        )

        medicines = [
            enrich(row)
            for row in rows
        ]

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

        database = get_db()

        medicine = database.medicines.find_one(
            {"id": id}
        )

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

        data = request.get_json() or {}

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
                    "message":
                        f"{field} is required"
                }), 400

        name = str(
            data["name"]
        ).strip()

        batch = str(
            data["batch_number"]
        ).strip()

        category = data["category"]

        manufacturer = str(
            data["manufacturer"]
        ).strip()

        mfg = data["manufacture_date"]
        exp = data["expiry_date"]

        quantity = int(
            data["quantity"]
        )

        price = float(
            data.get("unit_price", 0)
        )

        if quantity < 0:

            return jsonify({
                "success": False,
                "message":
                    "Quantity cannot be negative"
            }), 400

        mfg_date = datetime.strptime(
            mfg,
            "%Y-%m-%d"
        ).date()

        exp_date = datetime.strptime(
            exp,
            "%Y-%m-%d"
        ).date()

        if exp_date <= mfg_date:

            return jsonify({
                "success": False,
                "message":
                    "Expiry date must be after manufacture date"
            }), 400

        database = get_db()

        existing = database.medicines.find_one(
            {"batch_number": batch}
        )

        if existing:

            return jsonify({
                "success": False,
                "message":
                    "Batch number already exists"
            }), 409

        last = database.medicines.find_one(
            {},
            sort=[("id", -1)]
        )

        new_id = (
            (last.get("id", 0) + 1)
            if last
            else 1
        )

        medicine = {
            "id": new_id,
            "name": name,
            "batch_number": batch,
            "category": category,
            "manufacturer": manufacturer,
            "manufacture_date": mfg,
            "expiry_date": exp,
            "quantity": quantity,
            "unit_price": price,
            "added_on": datetime.utcnow()
        }

        database.medicines.insert_one(
            medicine
        )

        return jsonify({
            "success": True,
            "message":
                "Medicine added successfully",
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

        data = request.get_json() or {}

        database = get_db()

        existing = database.medicines.find_one(
            {"id": id}
        )

        if not existing:

            return jsonify({
                "success": False,
                "message":
                    "Medicine not found"
            }), 404

        name = str(
            data["name"]
        ).strip()

        batch = str(
            data["batch_number"]
        ).strip()

        category = data["category"]

        manufacturer = str(
            data["manufacturer"]
        ).strip()

        mfg = data["manufacture_date"]
        exp = data["expiry_date"]

        quantity = int(
            data["quantity"]
        )

        price = float(
            data.get("unit_price", 0)
        )

        if quantity < 0:

            return jsonify({
                "success": False,
                "message":
                    "Quantity cannot be negative"
            }), 400

        mfg_date = datetime.strptime(
            mfg,
            "%Y-%m-%d"
        ).date()

        exp_date = datetime.strptime(
            exp,
            "%Y-%m-%d"
        ).date()

        if exp_date <= mfg_date:

            return jsonify({
                "success": False,
                "message":
                    "Expiry date must be after manufacture date"
            }), 400

        duplicate = database.medicines.find_one({
            "batch_number": batch,
            "id": {"$ne": id}
        })

        if duplicate:

            return jsonify({
                "success": False,
                "message":
                    "Batch number already exists"
            }), 409

        database.medicines.update_one(
            {"id": id},
            {
                "$set": {
                    "name": name,
                    "batch_number": batch,
                    "category": category,
                    "manufacturer": manufacturer,
                    "manufacture_date": mfg,
                    "expiry_date": exp,
                    "quantity": quantity,
                    "unit_price": price
                }
            }
        )

        return jsonify({
            "success": True,
            "message":
                "Medicine updated successfully"
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

        database = get_db()

        result = database.medicines.delete_one(
            {"id": id}
        )

        if result.deleted_count == 0:

            return jsonify({
                "success": False,
                "message":
                    "Medicine not found"
            }), 404

        return jsonify({
            "success": True,
            "message":
                "Medicine deleted successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/api/dashboard", methods=["GET"])
def dashboard():

    try:

        database = get_db()

        medicines = [
            enrich(row)
            for row in database.medicines.find(
                {}
            ).sort(
                "expiry_date",
                1
            )
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

        state_rows = list(
            database.state_distribution.find({})
        )

        states_dict = {}

        for row in state_rows:

            state = row.get(
                "state_name",
                "Unknown"
            )

            if state not in states_dict:

                states_dict[state] = {
                    "state_name": state,
                    "medicine_ids": set(),
                    "total_qty": 0
                }

            states_dict[state][
                "medicine_ids"
            ].add(
                row.get("medicine_id")
            )

            states_dict[state][
                "total_qty"
            ] += int(
                row.get("quantity", 0)
            )

        states = []

        for state, value in states_dict.items():

            states.append({
                "state_name":
                    value["state_name"],
                "medicine_count":
                    len(value["medicine_ids"]),
                "total_qty":
                    value["total_qty"]
            })

        states.sort(
            key=lambda x: x["total_qty"],
            reverse=True
        )

        states = states[:8]

        transfers = list(
            database.transfers.find(
                {}
            ).sort(
                "transferred_on",
                -1
            ).limit(5)
        )

        transfer_list = []

        for t in transfers:

            medicine = database.medicines.find_one(
                {"id": t.get("medicine_id")}
            )

            transfer_list.append({
                "id": t.get("id"),
                "medicine_name":
                    medicine.get("name", "Unknown")
                    if medicine else "Unknown",
                "from_state":
                    t.get("from_state"),
                "to_state":
                    t.get("to_state"),
                "quantity":
                    t.get("quantity"),
                "transferred_on":
                    serialize(
                        t.get("transferred_on")
                    )
            })

        return jsonify({
            "success": True,
            "stats": stats,
            "medicines": medicines,
            "states": states,
            "transfers": transfer_list
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

        database = get_db()

        rows = list(
            database.state_distribution.find({})
        )

        result = []

        for row in rows:

            medicine = database.medicines.find_one(
                {"id": row.get("medicine_id")}
            )

            if not medicine:
                continue

            expiry = medicine.get(
                "expiry_date"
            )

            _, status = get_status(
                expiry
            )

            result.append({
                "state_name":
                    row.get("state_name"),
                "medicine_name":
                    medicine.get("name"),
                "category":
                    medicine.get("category"),
                "quantity":
                    row.get("quantity", 0),
                "distributed_on":
                    serialize(
                        row.get("distributed_on")
                    ),
                "expiry_date":
                    serialize(expiry),
                "status":
                    status
            })

        result.sort(
            key=lambda x: (
                x["state_name"],
                x["distributed_on"] or ""
            )
        )

        return jsonify({
            "success": True,
            "states": result
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

        data = request.get_json() or {}

        medicine_id = int(
            data["medicine_id"]
        )

        state_name = str(
            data["state_name"]
        ).strip()

        quantity = int(
            data["quantity"]
        )

        distributed_on = data.get(
            "distributed_on",
            str(date.today())
        )

        if not state_name:

            return jsonify({
                "success": False,
                "message":
                    "State name is required"
            }), 400

        if quantity <= 0:

            return jsonify({
                "success": False,
                "message":
                    "Quantity must be positive"
            }), 400

        database = get_db()

        medicine = database.medicines.find_one(
            {"id": medicine_id}
        )

        if not medicine:

            return jsonify({
                "success": False,
                "message":
                    "Medicine not found"
            }), 404

        available = int(
            medicine.get("quantity", 0)
        )

        if quantity > available:

            return jsonify({
                "success": False,
                "message":
                    f"Only {available} units available"
            }), 400

        last = database.state_distribution.find_one(
            {},
            sort=[("id", -1)]
        )

        new_id = (
            (last.get("id", 0) + 1)
            if last
            else 1
        )

        database.state_distribution.insert_one({
            "id": new_id,
            "medicine_id": medicine_id,
            "state_name": state_name,
            "quantity": quantity,
            "distributed_on": distributed_on
        })

        database.medicines.update_one(
            {"id": medicine_id},
            {
                "$inc": {
                    "quantity": -quantity
                }
            }
        )

        return jsonify({
            "success": True,
            "message":
                "Distribution recorded"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# TRANSFERS - GET
# ============================================================

@app.route("/api/transfers", methods=["GET"])
def get_transfers():

    try:

        database = get_db()

        rows = database.transfers.find(
            {}
        ).sort(
            "transferred_on",
            -1
        )

        transfers = []

        for row in rows:

            medicine = database.medicines.find_one(
                {"id": row.get("medicine_id")}
            )

            transfers.append({
                "id":
                    row.get("id"),
                "medicine_name":
                    medicine.get("name")
                    if medicine else "Unknown",
                "category":
                    medicine.get("category")
                    if medicine else "Other",
                "from_state":
                    row.get("from_state"),
                "to_state":
                    row.get("to_state"),
                "quantity":
                    row.get("quantity"),
                "transferred_on":
                    serialize(
                        row.get("transferred_on")
                    ),
                "notes":
                    row.get("notes", "")
            })

        return jsonify({
            "success": True,
            "transfers": transfers
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ============================================================
# TRANSFERS - POST
# ============================================================

@app.route("/api/transfers", methods=["POST"])
def add_transfer_api():

    try:

        data = request.get_json() or {}

        medicine_id = int(
            data["medicine_id"]
        )

        from_state = str(
            data["from_state"]
        ).strip()

        to_state = str(
            data["to_state"]
        ).strip()

        quantity = int(
            data["quantity"]
        )

        transferred_on = data.get(
            "transferred_on",
            str(date.today())
        )

        notes = str(
            data.get("notes", "")
        ).strip()

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

        database = get_db()

        medicine = database.medicines.find_one(
            {"id": medicine_id}
        )

        if not medicine:

            return jsonify({
                "success": False,
                "message":
                    "Medicine not found"
            }), 404

        last = database.transfers.find_one(
            {},
            sort=[("id", -1)]
        )

        new_id = (
            (last.get("id", 0) + 1)
            if last
            else 1
        )

        database.transfers.insert_one({
            "id": new_id,
            "medicine_id": medicine_id,
            "from_state": from_state,
            "to_state": to_state,
            "quantity": quantity,
            "transferred_on": transferred_on,
            "notes": notes
        })

        return jsonify({
            "success": True,
            "message":
                "Transfer recorded"
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
            data.get(
                "temperature",
                25
            )
        )

        humidity = float(
            data.get(
                "humidity",
                60
            )
        )

        light = data.get(
            "light_exposure",
            False
        )

        database = get_db()

        medicines = [
            enrich(row)
            for row in database.medicines.find({})
        ]

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
                "score":
                    score,
                "warnings":
                    warnings,
                "grade":
                    grade
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

        database = get_db()

        rows = list(
            database.medicines.find(
                {}
            ).sort(
                "expiry_date",
                1
            )
        )

        predictions = []

        for row in rows:

            row = clean_document(row)

            days, status = get_status(
                row["expiry_date"]
            )

            row["expiry_date"] = serialize(
                row["expiry_date"]
            )

            distributions = database.state_distribution.find(
                {
                    "medicine_id":
                        row["id"]
                }
            )

            distributed = sum(
                int(d.get("quantity", 0))
                for d in distributions
            )

            stock = int(
                row.get("quantity", 0)
            )

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

                daily_rate = (
                    distributed / 180
                )

                days_to_sell = int(
                    stock / daily_rate
                )

            else:

                days_to_sell = 999

            if days < 0:

                risk = "Expired"
                risk_color = "expired"

            elif (
                days_to_sell > days
                and days > 0
            ):

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
                "days":
                    days,
                "status":
                    status,
                "demand":
                    demand,
                "demand_score":
                    demand_score,
                "days_to_sell":
                    days_to_sell
                    if days_to_sell != 999
                    else "N/A",
                "distributed":
                    distributed,
                "risk":
                    risk,
                "risk_color":
                    risk_color,
                "info":
                    MEDICINE_INFO.get(
                        row.get("category"),
                        MEDICINE_INFO["Other"]
                    )
            })

        return jsonify({
            "success": True,
            "predictions":
                predictions
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

        database = get_db()

        rows = list(
            database.medicines.find({})
        )

        category_stats = {}

        for medicine in rows:

            category = medicine.get(
                "category",
                "Other"
            )

            if category not in category_stats:

                category_stats[category] = {
                    "category": category,
                    "count": 0,
                    "total_qty": 0
                }

            category_stats[category][
                "count"
            ] += 1

            category_stats[category][
                "total_qty"
            ] += int(
                medicine.get(
                    "quantity",
                    0
                )
            )

        return jsonify({
            "success": True,
            "medicine_info":
                MEDICINE_INFO,
            "category_stats":
                list(
                    category_stats.values()
                )
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

        database = get_db()

        rows = database.medicines.find(
            {
                "quantity": {
                    "$gt": 0
                }
            }
        ).sort([
            ("name", 1),
            ("expiry_date", 1)
        ])

        rows = [
            clean_document(row)
            for row in rows
        ]

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
                name,
                []
            ).append(row)

        fifo_list = []

        for name, batch_group in batches.items():

            sorted_batches = sorted(
                batch_group,
                key=lambda x:
                    x["expiry_date"]
            )

            for i, batch in enumerate(
                sorted_batches
            ):

                batch["fifo_order"] = i + 1

                batch["sell_first"] = (
                    i == 0
                )

                fifo_list.append(batch)

        fifo_list.sort(
            key=lambda x:
                x["expiry_date"]
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
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )