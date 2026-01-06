from db_connection import get_connection

def get_laws_by_domain(domain):
    """
    Fetches all legal rules for a given domain
    (RENT / EMPLOYMENT / CONSUMER)

    Returns:
        List of dictionaries containing law data
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all rules for the domain (no rule_type filtering)
    cursor.execute("""
        SELECT act_name, section, rule_text, risk_level
        FROM legal_rules
        WHERE domain = ?
    """, (domain,))

    rows = cursor.fetchall()
    conn.close()

    laws = []

    for row in rows:
        # Support for DB row objects or tuples
        if hasattr(row, 'act_name'):
            act_name = row.act_name
            section = row.section
            rule_text = row.rule_text
            risk_level = row.risk_level
        else:
            act_name, section, rule_text, risk_level = row[0], row[1], row[2], row[3]

        laws.append({
            "law_reference": f"{act_name} Section {section}",
            "rule_text": rule_text,
            "risk_level": risk_level
        })

    return laws


def get_relevant_laws(domain, clause, top_k=10):
    """
    Returns top_k laws in `domain` that match keywords
    extracted from `clause`. Uses SQL LIKE matching and basic ranking.
    """
    import re

    conn = get_connection()
    cursor = conn.cursor()

    # small stoplist and tokenization
    stopwords = {"the", "and", "for", "that", "with", "from", "this", "shall", "may", "must", "not", "any"}
    tokens = [w for w in re.findall(r"\w+", clause.lower()) if len(w) > 3 and w not in stopwords]

    if not tokens:
        # fallback: return all laws in domain
        return get_laws_by_domain(domain)

    # build SQL with multiple LIKE clauses for each token
    likes = " OR ".join(["rule_text LIKE ?"] * len(tokens))
    sql = f"""
        SELECT act_name, section, rule_text, risk_level
        FROM legal_rules
        WHERE domain = ? AND ({likes})
    """

    params = [domain] + [f"%{t}%" for t in tokens]
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    # simple ranking: count token occurrences in rule_text
    def score(row):
        rt = row.rule_text.lower()
        return sum(1 for t in tokens if t in rt)

    rows_sorted = sorted(rows, key=score, reverse=True)[:top_k]

    laws_out = []
    for row in rows_sorted:
        if hasattr(row, 'act_name'):
            act_name = row.act_name
            section = row.section
            rule_text = row.rule_text
            risk_level = row.risk_level
        else:
            act_name, section, rule_text, risk_level = row[0], row[1], row[2], row[3]

        laws_out.append({
            "law_reference": f"{act_name} Section {section}",
            "rule_text": rule_text,
            "risk_level": risk_level
        })

    return laws_out
