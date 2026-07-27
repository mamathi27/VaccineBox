from database import (
    get_connection,
    create_table,
    create_vaccine_table
)
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect



app = Flask(__name__)


create_table()
create_vaccine_table()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
def add_reading():

    if request.method == "POST":

        box_id = request.form["box_id"]
        temperature = float(request.form["temperature"])
        if temperature < -20 or temperature > 60:
            return "Invalid temperature! Reading rejected."
        location = request.form["location"]

        # Safe temperature range: 2°C to 8°C
        SAFE_MIN = 2
        SAFE_MAX = 6
        
        if SAFE_MIN <= temperature <= SAFE_MAX:
            breach_flag = "NO"
        else:
            breach_flag = "YES"

        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_connection()

        conn.execute("""
            INSERT INTO temperature_readings
            (box_id, temperature_c, breach_flag, location, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (box_id, temperature, breach_flag, location, recorded_at))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_reading.html")

@app.route("/readings")
def readings():

    search = request.args.get("search", "")

    conn = get_connection()

    if search:
        readings = conn.execute("""
            SELECT * FROM temperature_readings
            WHERE box_id LIKE ?
            ORDER BY reading_id DESC
        """, ('%' + search + '%',)).fetchall()
    else:
        readings = conn.execute("""
            SELECT * FROM temperature_readings
            ORDER BY reading_id DESC
        """).fetchall()

    conn.close()

    return render_template(
        "readings.html",
        readings=readings,
        search=search
    )
    
@app.route("/dashboard")
def dashboard():

    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM temperature_readings"
    ).fetchone()[0]

    safe = conn.execute(
        "SELECT COUNT(*) FROM temperature_readings WHERE breach_flag='NO'"
    ).fetchone()[0]

    breach = conn.execute(
        "SELECT COUNT(*) FROM temperature_readings WHERE breach_flag='YES'"
    ).fetchone()[0]

    avg = conn.execute(
        "SELECT AVG(temperature_c) FROM temperature_readings"
    ).fetchone()[0]

    recent = conn.execute("""
        SELECT *
        FROM temperature_readings
        ORDER BY reading_id DESC
        LIMIT 5
    """).fetchall()
    
    temperatures = []
    labels = []
    for row in reversed(recent):
        temperatures.append(row["temperature_c"])
        labels.append(row["box_id"])   
    
    vaccine_count = conn.execute(
        "SELECT COUNT(*) FROM vaccines"
    ).fetchone()[0]

    total_stock = conn.execute(
        "SELECT SUM(stock) FROM vaccines"
    ).fetchone()[0]

    if total_stock is None:
        total_stock = 0

    out_stock = conn.execute(
        "SELECT COUNT(*) FROM vaccines WHERE stock=0"
    ).fetchone()[0]

    expiring = conn.execute("""
        SELECT COUNT(*)
        FROM vaccines
        WHERE expiry_date <= date('now','+30 day')
        AND expiry_date >= date('now')
    """).fetchone()[0]

    stock_chart = conn.execute("""
        SELECT vaccine_name,stock
        FROM vaccines
    """).fetchall()

    stock_labels = []
    stock_values = []

    for row in stock_chart:
        stock_labels.append(row["vaccine_name"])
        stock_values.append(row["stock"])
    conn.close()

    if avg is None:
        avg = 0

    return render_template(
        "dashboard.html",
        total=total,
        safe=safe,
        breach=breach,
        avg=round(avg,2),
        recent=recent,
        temperatures=temperatures,
        labels=labels,
        vaccine_count=vaccine_count,
        total_stock=total_stock,
        out_stock=out_stock,
        expiring=expiring,
        stock_labels=stock_labels,
        stock_values=stock_values
    )

@app.route("/simulate")
def simulate():

    box_id = "BOX001"

    temperature = round(random.uniform(0, 10), 1)
    SAFE_MIN = 2
    SAFE_MAX = 6
    if SAFE_MIN <= temperature <= SAFE_MAX:
        breach_flag = "NO"
    else:
        breach_flag = "YES"

    location = random.choice([
        "District Store",
        "Village A",
        "Village B",
        "PHC Center"
    ])

    recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()

    conn.execute("""
        INSERT INTO temperature_readings
        (box_id, temperature_c, breach_flag, location, recorded_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        box_id,
        temperature,
        breach_flag,
        location,
        recorded_at
    ))

    conn.commit()
    conn.close()

    return f"""
    <h2>Sensor Reading Added</h2>

    <p>Temperature: {temperature} °C</p>

    <p>Breach: {breach}</p>

    <a href='/dashboard'>Dashboard</a>
    """
    
@app.route("/inventory")
def inventory():

    conn = get_connection()

    vaccines = conn.execute("""
        SELECT *
        FROM vaccines
        ORDER BY expiry_date
    """).fetchall()

    conn.close()

    today = datetime.today().date()

    vaccine_list = []

    for vaccine in vaccines:

        expiry = datetime.strptime(
            vaccine["expiry_date"],
            "%Y-%m-%d"
        ).date()

        days_left = (expiry - today).days

        if days_left < 0:
            status = "Expired"

        elif days_left <= 30:
            status = "Expiring Soon"

        else:
            status = "Safe"

        vaccine_list.append({

            "vaccine_id": vaccine["vaccine_id"],
            "vaccine_name": vaccine["vaccine_name"],
            "manufacturer": vaccine["manufacturer"],
            "batch_number": vaccine["batch_number"],
            "stock": vaccine["stock"],
            "expiry_date": vaccine["expiry_date"],
            "days_left": days_left,
            "status": status

        })
    print(vaccine_list)

    return render_template(
        "inventory.html",
        vaccines=vaccine_list
    ) 
@app.route("/delete-vaccine/<int:id>")
def delete_vaccine(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM vaccines WHERE vaccine_id=?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect("/inventory")
@app.route("/edit-vaccine/<int:id>", methods=["GET", "POST"])
def edit_vaccine(id):

    conn = get_connection()

    if request.method == "POST":

        conn.execute("""

        UPDATE vaccines

        SET

        vaccine_name=?,

        manufacturer=?,

        batch_number=?,

        stock=?,

        expiry_date=?

        WHERE vaccine_id=?

        """,(

        request.form["vaccine_name"],
        request.form["manufacturer"],
        request.form["batch_number"],
        request.form["stock"],
        request.form["expiry_date"],
        id

        ))

        conn.commit()

        conn.close()

        return redirect("/inventory")

    vaccine = conn.execute(

        "SELECT * FROM vaccines WHERE vaccine_id=?",

        (id,)

    ).fetchone()

    conn.close()

    return render_template(
        "edit_vaccine.html",
        vaccine=vaccine
    )

if __name__ == "__main__":
    app.run(debug=True)