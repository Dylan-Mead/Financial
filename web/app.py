"""Minimal Flask web app to view collected data and plots."""
from flask import Flask, render_template_string, send_from_directory
from src.db.pg import query_to_dataframe, get_engine
from src.visualization.plots import plot_price_series

app = Flask(__name__, static_folder="static")

INDEX_HTML = """
<!doctype html>
<title>Financial Data</title>
<h1>Collected Data</h1>
<p>Latest data table (rendered as text) and price plot below.</p>
<div>
<img src="/static/price_series.png" alt="price plot" style="max-width:100%">
</div>
<pre>{{ table_html }}</pre>
"""

@app.route("/")
def index():
    try:
        df = query_to_dataframe(limit=100, engine=get_engine())
        plot_price_series(df)
        table_html = df.to_string()
    except Exception as e:
        table_html = f"Error fetching data: {e}\n"
    return render_template_string(INDEX_HTML, table_html=table_html)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
