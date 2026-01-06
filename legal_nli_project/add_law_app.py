from flask import Flask, render_template, request, redirect
from db_connection import get_connection

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def add_law():
    if request.method == 'POST':
        act_name = request.form['act_name']
        section = request.form['section']
        rule_text = request.form['rule_text']
    
        domain = request.form.get('domain')
        # risk_level comes from the form; default to MEDIUM if not provided
        risk_level = request.form.get('risk_level', 'MEDIUM')

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO legal_rules (act_name, section, rule_text, risk_level, domain)
            VALUES (?, ?, ?, ?, ?)
        """, (act_name, section, rule_text, risk_level, domain))
        conn.commit()
        conn.close()
        return redirect('/')  # reload page after inserting

    return render_template('add_law.html')

if __name__ == '__main__':
    app.run(debug=True)
