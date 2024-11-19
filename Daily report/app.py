from flask import Flask, render_template, request, jsonify
from prtgdata import search_device, write_combined_report, generate_critical_sites_report, prtg_servers
from flask_apscheduler import APScheduler

app = Flask(__name__)

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

scheduler = APScheduler()

@scheduler.task('interval', id='generate_reports_task', hours=15)
def scheduled_generate_reports():
    combined_report_path = "Combined_PRTG_Report.txt"
    critical_sites_report_path = "Critical_Sites_Report.txt"
    write_combined_report(prtg_servers)
    generate_critical_sites_report(combined_report_path, critical_sites_report_path)
    print("Scheduled reports generated.")

scheduler.init_app(app)
scheduler.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_term = request.json.get('search_term')
    results = search_device(prtg_servers, search_term)
    return jsonify(results)

@app.route('/generate_reports', methods=['POST'])
def generate_reports():
    combined_report_path = "Combined_PRTG_Report.txt"
    critical_sites_report_path = "Critical_Sites_Report.txt"
    write_combined_report(prtg_servers)
    generate_critical_sites_report(combined_report_path, critical_sites_report_path)
    
    with open(critical_sites_report_path, 'r') as file:
        report_data = file.read()
    
    return jsonify({"report": report_data})

if __name__ == '__main__':
    app.run(debug=True)