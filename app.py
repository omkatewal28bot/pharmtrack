from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import date, datetime
import os
import traceback

# ============================================================
# PHARMTRACK
# Flask + MongoDB Atlas + Netlify
# ============================================================

app = Flask(__name__)

# ============================================================
# CORS
# ============================================================

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*"
        }
    },
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# ============================================================
# MONGODB CONFIGURATION
# ============================================================

MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB = os.environ.get("MONGODB_DB", "pharmtrack")

client = None
db = None


def get_db():
    global client, db

    if not MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI is missing in Render Environment Variables"
        )

    if client is None:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True
        )

    # Force MongoDB connection test
    client.admin.command("ping")

    if db is None:
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

def error_response(message, status=500):
    return jsonify({
        "success": False,
        "message": str(message)
    }), status


def parse_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, dict) and "$date" in value:
        value = value["$date"]

    if isinstance(value, str):
        value = value[:10]
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

    raise ValueError(
        f"Invalid date value: {value}"
    )


def serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return value


def clean_document(doc):
    if not doc:
        return None

    doc = dict(doc)

    # MongoDB ObjectId should not go to frontend
    doc.pop("_id", None)

    return doc


def get_status(expiry_date):
    try:
        expiry = parse_date(expiry_date)

        if not expiry:
            return 0, "safe"

        days = (
            expiry - date.today()
        ).days

        if days < 0:
            return days, "expired"

        if days <= 30:
            return days, "critical"

        if days <= 90:
            return days, "warning"

        return days, "safe"

    except Exception as e:
        print("Status calculation error:", e)
        return 0, "safe"


def enrich(medicine):
    medicine = clean_document(medicine)

    if not medicine:
        return None

    days, status = get_status(
        medicine.get("expiry_date")
    )

    medicine["days"] = days
    medicine["status"] = status

    for key in [
        "expiry_date",
        "manufacture_date",
        "added_on"
    ]:
        if key in medicine:
            medicine[key] = serialize(
                medicine[key]
            )

    category = medicine.get(
        "category",
        "Other"
    )

    medicine["info"] = MEDICINE_INFO.get(
        category,
        MEDICINE_INFO["Other"]
    )

    return medicine


def get_next_id(collection):
    last = collection.find_one(
        {},
        sort=[("id", -1)]
    )

    if not last:
        return 1

    try:
        return int(last.get("id", 0)) + 1
    except Exception:
        return 1


# ============================================================
# USABILITY CALCULATION
# ============================================================

def get_usability_score(
    medicine,
    temp=25,
    humidity=60,
    light_exposure=False
):

    category = medicine.get(
        "category",
        "Other"
    )

    info = MEDICINE_INFO.get(
        category,
        MEDICINE_INFO["Other"]
    )

    score = 100
    warnings = []

    days = medicine.get("days", 0)

    # Expiry
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

    # Temperature
    try:

        temp_text = info["temp"]

        numbers = (
            temp_text
            .replace("°C", "")
            .split("-")
        )

        temp_min = float(numbers[0])
        temp_max = float(numbers[1])

        if temp < temp_min or temp > temp_max:

            score -= 25

            warnings.append(
                f"Temperature {temp}°C out of range "
                f"({info['temp']})"
            )

    except Exception as e:
        print("Temperature check error:", e)

    # Humidity
    try:

        max_humidity = float(
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

    except Exception as e:
        print("Humidity check error:", e)

    # Light
    if light_exposure:

        light_text = info["light"].lower()

        if "dark" in light_text:

            score -= 15

            warnings.append(
                "Light exposure detected — "
                "store in dark place"
            )

        elif "sunlight" in light_text:

            score -= 10

            warnings.append(
                "Avoid direct sunlight exposure"
            )

    score = max(
        0,
        min(100, score)
    )

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

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "PharmTrack API is running",
        "frontend": "Netlify",
        "backend": "Render",
        "database": "MongoDB Atlas"
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    try:

        if not MONGODB_URI:

            return jsonify({
                "success": False,
                "database": "not_configured",
                "message":
                    "MONGODB_URI is missing in Render Environment Variables"
            }), 500

        database = get_db()

        database.command("ping")

        collections = database.list_collection_names()

        return jsonify({
            "success": True,
            "database": "connected",
            "database_type": "MongoDB Atlas",
            "database_name": MONGODB_DB,
            "collections": collections,
            "message":
                "Backend and MongoDB are connected"
        }), 200

    except Exception as e:

        print("======================================")
        print("MONGODB HEALTH CHECK ERROR")
        print("======================================")
        print(str(e))
        traceback.print_exc()

        return jsonify({
            "success": False,
            "database": "error",
            "database_type": "MongoDB Atlas",
            "message": str(e)
        }), 500


# ============================================================
# MEDICINES - GET ALL
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

        medicines = []

        for row in rows:

            medicine = enrich(row)

            if medicine:
                medicines.append(medicine)

        return jsonify({
            "success": True,
            "medicines": medicines
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# MEDICINE - GET SINGLE
# ============================================================

@app.route(
    "/api/medicines/<int:id>",
    methods=["GET"]
)
def get_medicine(id):

    try:

        database = get_db()

        medicine = database.medicines.find_one({
            "id": id
        })

        if not medicine:

            return error_response(
                "Medicine not found",
                404
            )

        return jsonify({
            "success": True,
            "medicine": enrich(medicine)
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# MEDICINE - ADD
# ============================================================

@app.route(
    "/api/medicines",
    methods=["POST"]
)
def add_medicine():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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

            if (
                field not in data
                or data[field] in ["", None]
            ):

                return error_response(
                    f"{field} is required",
                    400
                )

        name = str(
            data["name"]
        ).strip()

        batch = str(
            data["batch_number"]
        ).strip()

        category = str(
            data["category"]
        ).strip()

        manufacturer = str(
            data["manufacturer"]
        ).strip()

        quantity = int(
            data["quantity"]
        )

        price = float(
            data.get(
                "unit_price",
                data.get("price", 0)
            )
        )

        if quantity < 0:

            return error_response(
                "Quantity cannot be negative",
                400
            )

        if price < 0:

            return error_response(
                "Price cannot be negative",
                400
            )

        mfg_date = parse_date(
            data["manufacture_date"]
        )

        exp_date = parse_date(
            data["expiry_date"]
        )

        if exp_date <= mfg_date:

            return error_response(
                "Expiry date must be after manufacture date",
                400
            )

        database = get_db()

        existing = database.medicines.find_one({
            "batch_number": batch
        })

        if existing:

            return error_response(
                "Batch number already exists",
                409
            )

        new_id = get_next_id(
            database.medicines
        )

        medicine = {
            "id": new_id,
            "name": name,
            "batch_number": batch,
            "category": category,
            "manufacturer": manufacturer,
            "manufacture_date":
                mfg_date.isoformat(),
            "expiry_date":
                exp_date.isoformat(),
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

    except ValueError as e:

        return error_response(
            f"Invalid input: {e}",
            400
        )

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# MEDICINE - UPDATE
# ============================================================

@app.route(
    "/api/medicines/<int:id>",
    methods=["PUT"]
)
def update_medicine(id):

    try:

        data = request.get_json(
            silent=True
        ) or {}

        database = get_db()

        existing = database.medicines.find_one({
            "id": id
        })

        if not existing:

            return error_response(
                "Medicine not found",
                404
            )

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

            if (
                field not in data
                or data[field] in ["", None]
            ):

                return error_response(
                    f"{field} is required",
                    400
                )

        name = str(
            data["name"]
        ).strip()

        batch = str(
            data["batch_number"]
        ).strip()

        category = str(
            data["category"]
        ).strip()

        manufacturer = str(
            data["manufacturer"]
        ).strip()

        quantity = int(
            data["quantity"]
        )

        price = float(
            data.get(
                "unit_price",
                data.get("price", 0)
            )
        )

        if quantity < 0:

            return error_response(
                "Quantity cannot be negative",
                400
            )

        mfg_date = parse_date(
            data["manufacture_date"]
        )

        exp_date = parse_date(
            data["expiry_date"]
        )

        if exp_date <= mfg_date:

            return error_response(
                "Expiry date must be after manufacture date",
                400
            )

        duplicate = database.medicines.find_one({
            "batch_number": batch,
            "id": {"$ne": id}
        })

        if duplicate:

            return error_response(
                "Batch number already exists",
                409
            )

        database.medicines.update_one(
            {"id": id},
            {
                "$set": {
                    "name": name,
                    "batch_number": batch,
                    "category": category,
                    "manufacturer": manufacturer,
                    "manufacture_date":
                        mfg_date.isoformat(),
                    "expiry_date":
                        exp_date.isoformat(),
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

    except ValueError as e:

        return error_response(
            f"Invalid input: {e}",
            400
        )

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# MEDICINE - DELETE
# ============================================================

@app.route(
    "/api/medicines/<int:id>",
    methods=["DELETE"]
)
def delete_medicine(id):

    try:

        database = get_db()

        result = database.medicines.delete_one({
            "id": id
        })

        if result.deleted_count == 0:

            return error_response(
                "Medicine not found",
                404
            )

        # Remove related distribution records
        database.state_distribution.delete_many({
            "medicine_id": id
        })

        # Remove related transfer records
        database.transfers.delete_many({
            "medicine_id": id
        })

        return jsonify({
            "success": True,
            "message":
                "Medicine deleted successfully"
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# DASHBOARD
# ============================================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    try:

        database = get_db()

        rows = database.medicines.find(
            {}
        ).sort(
            "expiry_date",
            1
        )

        medicines = []

        for row in rows:

            medicine = enrich(row)

            if medicine:
                medicines.append(medicine)

        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # STATES
        # ----------------------------------------------------

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

            medicine_id = row.get(
                "medicine_id"
            )

            if medicine_id is not None:

                states_dict[state][
                    "medicine_ids"
                ].add(medicine_id)

            try:

                states_dict[state][
                    "total_qty"
                ] += int(
                    row.get(
                        "quantity",
                        0
                    )
                )

            except Exception:
                pass

        states = []

        for value in states_dict.values():

            states.append({
                "state_name":
                    value["state_name"],
                "medicine_count":
                    len(
                        value["medicine_ids"]
                    ),
                "total_qty":
                    value["total_qty"]
            })

        states.sort(
            key=lambda x:
                x["total_qty"],
            reverse=True
        )

        states = states[:8]

        # ----------------------------------------------------
        # TRANSFERS
        # ----------------------------------------------------

        transfer_rows = list(
            database.transfers.find(
                {}
            ).sort(
                "transferred_on",
                -1
            ).limit(5)
        )

        transfer_list = []

        for transfer in transfer_rows:

            medicine = database.medicines.find_one({
                "id":
                    transfer.get(
                        "medicine_id"
                    )
            })

            transfer_list.append({
                "id":
                    transfer.get("id"),

                "medicine_name":
                    medicine.get(
                        "name",
                        "Unknown"
                    )
                    if medicine
                    else "Unknown",

                "from_state":
                    transfer.get(
                        "from_state",
                        ""
                    ),

                "to_state":
                    transfer.get(
                        "to_state",
                        ""
                    ),

                "quantity":
                    transfer.get(
                        "quantity",
                        0
                    ),

                "transferred_on":
                    serialize(
                        transfer.get(
                            "transferred_on"
                        )
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

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# STATES - GET
# ============================================================

@app.route(
    "/api/states",
    methods=["GET"]
)
def get_states():

    try:

        database = get_db()

        rows = list(
            database.state_distribution.find({})
        )

        result = []

        for row in rows:

            medicine = database.medicines.find_one({
                "id":
                    row.get(
                        "medicine_id"
                    )
            })

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
                    row.get(
                        "state_name",
                        ""
                    ),

                "medicine_name":
                    medicine.get(
                        "name",
                        ""
                    ),

                "category":
                    medicine.get(
                        "category",
                        "Other"
                    ),

                "quantity":
                    row.get(
                        "quantity",
                        0
                    ),

                "distributed_on":
                    serialize(
                        row.get(
                            "distributed_on"
                        )
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

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# DISTRIBUTION
# ============================================================

@app.route(
    "/api/distribute",
    methods=["POST"]
)
def distribute():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        required = [
            "medicine_id",
            "state_name",
            "quantity"
        ]

        for field in required:

            if (
                field not in data
                or data[field] in ["", None]
            ):

                return error_response(
                    f"{field} is required",
                    400
                )

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
            date.today().isoformat()
        )

        if not state_name:

            return error_response(
                "State name is required",
                400
            )

        if quantity <= 0:

            return error_response(
                "Quantity must be positive",
                400
            )

        database = get_db()

        medicine = database.medicines.find_one({
            "id": medicine_id
        })

        if not medicine:

            return error_response(
                "Medicine not found",
                404
            )

        available = int(
            medicine.get(
                "quantity",
                0
            )
        )

        if quantity > available:

            return error_response(
                f"Only {available} units available",
                400
            )

        new_id = get_next_id(
            database.state_distribution
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
        }), 201

    except ValueError as e:

        return error_response(
            f"Invalid input: {e}",
            400
        )

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# TRANSFERS - GET
# ============================================================

@app.route(
    "/api/transfers",
    methods=["GET"]
)
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

            medicine = database.medicines.find_one({
                "id":
                    row.get(
                        "medicine_id"
                    )
            })

            transfers.append({
                "id":
                    row.get("id"),

                "medicine_name":
                    medicine.get(
                        "name",
                        "Unknown"
                    )
                    if medicine
                    else "Unknown",

                "category":
                    medicine.get(
                        "category",
                        "Other"
                    )
                    if medicine
                    else "Other",

                "from_state":
                    row.get(
                        "from_state",
                        ""
                    ),

                "to_state":
                    row.get(
                        "to_state",
                        ""
                    ),

                "quantity":
                    row.get(
                        "quantity",
                        0
                    ),

                "transferred_on":
                    serialize(
                        row.get(
                            "transferred_on"
                        )
                    ),

                "notes":
                    row.get(
                        "notes",
                        ""
                    )
            })

        return jsonify({
            "success": True,
            "transfers": transfers
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# TRANSFERS - POST
# ============================================================

@app.route(
    "/api/transfers",
    methods=["POST"]
)
def add_transfer_api():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        required = [
            "medicine_id",
            "from_state",
            "to_state",
            "quantity"
        ]

        for field in required:

            if (
                field not in data
                or data[field] in ["", None]
            ):

                return error_response(
                    f"{field} is required",
                    400
                )

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
            date.today().isoformat()
        )

        notes = str(
            data.get(
                "notes",
                ""
            )
        ).strip()

        if not from_state or not to_state:

            return error_response(
                "From state and To state are required",
                400
            )

        if from_state == to_state:

            return error_response(
                "From and To states cannot be same",
                400
            )

        if quantity <= 0:

            return error_response(
                "Quantity must be positive",
                400
            )

        database = get_db()

        medicine = database.medicines.find_one({
            "id": medicine_id
        })

        if not medicine:

            return error_response(
                "Medicine not found",
                404
            )

        new_id = get_next_id(
            database.transfers
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

    except ValueError as e:

        return error_response(
            f"Invalid input: {e}",
            400
        )

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# USABILITY
# ============================================================

@app.route(
    "/api/usability",
    methods=["POST"]
)
def usability_api():

    try:

        data = request.get_json(
            silent=True
        ) or {}

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

        light = bool(
            data.get(
                "light_exposure",
                False
            )
        )

        database = get_db()

        medicines = []

        for row in database.medicines.find({}):

            medicine = enrich(row)

            if medicine:
                medicines.append(medicine)

        results = []

        for medicine in medicines:

            score, warnings, grade = get_usability_score(
                medicine,
                temp,
                humidity,
                light
            )

            results.append({
                **medicine,
                "score": score,
                "warnings": warnings,
                "grade": grade
            })

        results.sort(
            key=lambda x:
                x["score"]
        )

        return jsonify({
            "success": True,
            "temperature": temp,
            "humidity": humidity,
            "light_exposure": light,
            "results": results
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# PREDICTION
# ============================================================

@app.route(
    "/api/prediction",
    methods=["GET"]
)
def prediction_api():

    try:

        database = get_db()

        rows = database.medicines.find(
            {}
        ).sort(
            "expiry_date",
            1
        )

        predictions = []

        for original_row in rows:

            row = clean_document(
                original_row
            )

            if not row:
                continue

            days, status = get_status(
                row.get(
                    "expiry_date"
                )
            )

            row["expiry_date"] = serialize(
                row.get(
                    "expiry_date"
                )
            )

            distributions = database.state_distribution.find({
                "medicine_id":
                    row.get("id")
            })

            distributed = 0

            for distribution in distributions:

                try:
                    distributed += int(
                        distribution.get(
                            "quantity",
                            0
                        )
                    )
                except Exception:
                    pass

            stock = int(
                row.get(
                    "quantity",
                    0
                )
            )

            # Demand
            if distributed == 0:

                demand = "Low"
                demand_score = 1

            elif distributed < 50:

                demand = "Medium"
                demand_score = 2

            else:

                demand = "High"
                demand_score = 3

            # Days to sell
            if distributed > 0 and stock > 0:

                daily_rate = (
                    distributed / 180
                )

                if daily_rate > 0:

                    days_to_sell = int(
                        stock / daily_rate
                    )

                else:
                    days_to_sell = 999

            else:

                days_to_sell = 999

            # Risk
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

                "days": days,

                "status": status,

                "demand": demand,

                "demand_score":
                    demand_score,

                "days_to_sell":
                    days_to_sell
                    if days_to_sell != 999
                    else "N/A",

                "distributed":
                    distributed,

                "risk": risk,

                "risk_color":
                    risk_color,

                "info":
                    MEDICINE_INFO.get(
                        row.get(
                            "category",
                            "Other"
                        ),
                        MEDICINE_INFO["Other"]
                    )
            })

        return jsonify({
            "success": True,
            "predictions": predictions
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# KNOWLEDGE
# ============================================================

@app.route(
    "/api/knowledge",
    methods=["GET"]
)
def knowledge_api():

    try:

        database = get_db()

        rows = database.medicines.find({})

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

            try:

                category_stats[category][
                    "total_qty"
                ] += int(
                    medicine.get(
                        "quantity",
                        0
                    )
                )

            except Exception:
                pass

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

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# FIFO
# ============================================================

@app.route(
    "/api/fifo",
    methods=["GET"]
)
def fifo_api():

    try:

        database = get_db()

        rows = database.medicines.find({
            "quantity": {
                "$gt": 0
            }
        }).sort([
            ("name", 1),
            ("expiry_date", 1)
        ])

        batches = {}

        for original_row in rows:

            row = clean_document(
                original_row
            )

            if not row:
                continue

            days, status = get_status(
                row.get(
                    "expiry_date"
                )
            )

            row["expiry_date"] = serialize(
                row.get(
                    "expiry_date"
                )
            )

            row["manufacture_date"] = serialize(
                row.get(
                    "manufacture_date"
                )
            )

            row["days"] = days
            row["status"] = status

            medicine_name = str(
                row.get(
                    "name",
                    "Unknown"
                )
            )

            # Group by complete medicine name
            name = medicine_name.strip()

            batches.setdefault(
                name,
                []
            ).append(row)

        fifo_list = []

        for name, batch_group in batches.items():

            sorted_batches = sorted(
                batch_group,
                key=lambda x:
                    x.get(
                        "expiry_date",
                        ""
                    )
            )

            for index, batch in enumerate(
                sorted_batches
            ):

                batch["fifo_order"] = (
                    index + 1
                )

                batch["sell_first"] = (
                    index == 0
                )

                fifo_list.append(
                    batch
                )

        fifo_list.sort(
            key=lambda x:
                x.get(
                    "expiry_date",
                    ""
                )
        )

        return jsonify({
            "success": True,
            "batches": batches,
            "fifo_list": fifo_list
        })

    except Exception as e:

        traceback.print_exc()

        return error_response(
            str(e)
        )


# ============================================================
# OLD API COMPATIBILITY
# ============================================================

@app.route(
    "/api",
    methods=["GET"]
)
def old_api():

    return get_medicines()


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "success": False,
        "message": "API endpoint not found",
        "path": request.path
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({
        "success": False,
        "message": "HTTP method not allowed",
        "method": request.method,
        "path": request.path
    }), 405


@app.errorhandler(500)
def internal_error(error):

    print("GLOBAL SERVER ERROR:")
    traceback.print_exc()

    return jsonify({
        "success": False,
        "message": "Internal server error"
    }), 500


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

    print("======================================")
    print("        PHARMTRACK BACKEND")
    print("======================================")
    print(f"Port: {port}")
    print(
        f"Database: {MONGODB_DB}"
    )
    print(
        "MongoDB URI configured:",
        bool(MONGODB_URI)
    )
    print("======================================")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )