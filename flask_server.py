from flask import Flask, render_template_string, request
from threading import Lock

app = Flask(__name__)

# Almacenar las imágenes y datos con un bloqueo para acceso concurrente
data = {
    "main_deck_base64": None,
    "lower_decks_base64": None,
    "total_carga": 0.0,
    "tow_cg": 0.0,
    "lateral_imbalance": 0.0,
    "pallets_imbalance": 0.0,
    "zfw_cg": 0.0,
    "lw_cg": 0.0
}
data_lock = Lock()

@app.route('/pallet_distribution', methods=['GET'])
def pallet_distribution():
    with data_lock:
        main_deck_base64 = data["main_deck_base64"]
        lower_decks_base64 = data["lower_decks_base64"]
        total_carga = data["total_carga"]
        tow_cg = data["tow_cg"]
        lateral_imbalance = data["lateral_imbalance"]
        pallets_imbalance = data["pallets_imbalance"]
        zfw_cg = data["zfw_cg"]
        lw_cg = data["lw_cg"]
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Distribución de Pallets</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f4;
            }}
            .header {{
                background-color: #e0e0e0;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .header p {{
                margin: 5px 0;
                font-size: 16px;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            }}
            .deck {{
                width: 80%;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .deck img {{
                max-width: 100%;
                height: auto;
            }}
            .deck h2 {{
                color: #333;
                margin-bottom: 10px;
            }}
        </style>
        <script>
            // Recargar la página cada 10 segundos
            setInterval(function() {{
                location.reload();
            }}, 10000);
        </script>
    </head>
    <body>
        <h1>Distribución de Pallets</h1>
        <p>Esta página se actualiza automáticamente cada 10 segundos.</p>
        <div class="header">
            <p><strong>Peso Total Carga Asignada:</strong> {total_carga:,.1f} kg</p>
            <p><strong>TOW CG:</strong> {tow_cg:,.1f}% MAC</p>
            <p><strong>Desbalance Lateral:</strong> {lateral_imbalance:,.1f} kg.m</p>
            <p><strong>Desbalance de Pallets (MD, LDA, LDF):</strong> {pallets_imbalance:,.1f} kg</p>
            <p><strong>ZFW CG:</strong> {zfw_cg:,.1f}% MAC</p>
            <p><strong>LW CG:</strong> {lw_cg:,.1f}% MAC</p>
        </div>
        <div class="container">
            <div class="deck">
                <h2>Main Deck (MD)</h2>
                {"<img src='data:image/png;base64," + main_deck_base64 + "' alt='Main Deck'>" if main_deck_base64 else "<p>No disponible</p>"}
            </div>
            <div class="deck">
                <h2>Lower Decks (LDF/LDA)</h2>
                {"<img src='data:image/png;base64," + lower_decks_base64 + "' alt='Lower Decks'>" if lower_decks_base64 else "<p>No disponible</p>"}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.route('/update_images', methods=['POST'])
def update_images():
    received_data = request.get_json()
    with data_lock:
        data["main_deck_base64"] = received_data.get("main_deck_base64")
        data["lower_decks_base64"] = received_data.get("lower_decks_base64")
        data["total_carga"] = received_data.get("total_carga", 0.0)
        data["tow_cg"] = received_data.get("tow_cg", 0.0)
        data["lateral_imbalance"] = received_data.get("lateral_imbalance", 0.0)
        data["pallets_imbalance"] = received_data.get("pallets_imbalance", 0.0)
        data["zfw_cg"] = received_data.get("zfw_cg", 0.0)
        data["lw_cg"] = received_data.get("lw_cg", 0.0)
    return {"status": "success"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)