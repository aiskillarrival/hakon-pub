# Web Scraper + Live Dashboard
Project: Track Something You Care About (Prices, Weather, Ratings, Anything)
Multiple components: scraping, storing, analyzing, and visualizing data.

⭐ Core Idea
Build a system that automatically collects data from the web every day (or 
every hour) and displays it on a dashboard with charts, trends, and alerts.

Examples:

- GPU or laptop prices
- Book ratings
- Weather patterns
- Game patch notes
- Cryptocurrency prices
- Anything with a predictable URL


To move from printing using print to displaying on a web page, 
refactor your script's logic to return data instead of calling print(), 
then pass that data to Flask's Jinja2 template renderer.

1. Set Up the Directory Structure
Organize your project folder so Flask knows where to locate your HTML files:

my_project/
│── app.py
└── templates/
└── index.html
2. Refactor Your Python Code (app.py)
Replace your print() statements with return values (dictionaries, lists, or strings), then inject them into the route handler.

from flask import Flask, render_template

app = Flask(__name__)

def get_system_info():
# Return data instead of using print()
return {
"status": "System Operational",
"logs": ["Disk usage: 42%", "Memory usage: 64%", "Uptime: 12 hrs"]
}

@app.route("/")
def home():
data = get_system_info()
return render_template("index.html", content=data)

if __name__ == "__main__":
app.run(debug=True)
3. Create the HTML Template (templates/index.html)
Use Jinja2 tags ({{ ... }} for variables and {% ... %} for control flow) to render the data in HTML.

<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>System Dashboard</title>
</head>
<body>
<h1>Status: {{ content.status }}</h1>
<ul>
{% for log in content.logs %}
<li>{{ log }}</li>
{% endfor %}
</ul>
</body>
</html>
Alternative: Quick Stdout Capture
If refactoring legacy print() functions is too time-consuming, capture the stdout buffer directly in Python and send the raw text block to your template:

import io
import sys
from flask import Flask, render_template

app = Flask(__name__)

def legacy_script():
print("System Check Complete.")
print("All modules loaded successfully.")

@app.route("/")
def home():
old_stdout = sys.stdout
sys.stdout = buffer = io.StringIO()

legacy_script() # Runs prints into buffer

sys.stdout = old_stdout # Reset stdout
output = buffer.getvalue()

return render_template("index.html", raw_output=output)
Display raw output inside a <pre> tag in index.html to preserve line breaks and formatting:

<pre>{{ raw_output }}</pre>
Run python app.py in your terminal and open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.


