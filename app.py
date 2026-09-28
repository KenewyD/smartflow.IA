
import io
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = "smartflow.db"

st.set_page_config(page_title="SmartFlow AI", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
.metric-card {border:1px solid #e5e7eb; border-radius:14px; padding:14px; background:white;}
.small {color:#6b7280;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

st.title("⚙️ SmartFlow AI")
st.caption("Automatisation intelligente d'un processus de gestion : extraction, contrôle, validation et suivi de factures.")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            supplier TEXT,
            invoice_date TEXT,
            invoice_number TEXT,
            amount_ht REAL,
            vat REAL,
            amount_ttc REAL,
            category TEXT,
            object_text TEXT,
            status TEXT,
            risk_flag TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn

def parse_invoice_text(text, filename="document"):
    def grab(pattern, default=""):
        m = re.search(pattern, text, flags=re.I)
        return m.group(1).strip() if m else default

    supplier = grab(r"Fournisseur\s*:\s*(.+)")
    invoice_date = grab(r"Date\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
    invoice_number = grab(r"Numero\s*:\s*(.+)")
    amount_ht = grab(r"Montant HT\s*:\s*([0-9\.,]+)")
    vat = grab(r"TVA\s*:\s*([0-9\.,]+)")
    amount_ttc = grab(r"Montant TTC\s*:\s*([0-9\.,]+)")
    category = grab(r"Categorie\s*:\s*(.+)")
    object_text = grab(r"Objet\s*:\s*(.+)")

    def to_float(x):
        try:
            return float(x.replace(",", "."))
        except:
            return None

    parsed = {
        "filename": filename,
        "supplier": supplier,
        "invoice_date": invoice_date,
        "invoice_number": invoice_number,
        "amount_ht": to_float(amount_ht),
        "vat": to_float(vat),
        "amount_ttc": to_float(amount_ttc),
        "category": category,
        "object_text": object_text
    }
    return parsed

def validate_invoice(inv):
    issues = []
    if not inv["supplier"]:
        issues.append("Fournisseur manquant")
    if not inv["invoice_date"]:
        issues.append("Date manquante")
    if not inv["invoice_number"]:
        issues.append("Numéro de facture manquant")
    if inv["amount_ht"] is None:
        issues.append("Montant HT manquant")
    if inv["vat"] is None:
        issues.append("TVA manquante")
    if inv["amount_ttc"] is None:
        issues.append("Montant TTC manquant")

    if all(inv[k] is not None for k in ["amount_ht","vat","amount_ttc"]):
        expected = round(inv["amount_ht"] + inv["vat"], 2)
        if abs(expected - inv["amount_ttc"]) > 0.05:
            issues.append("Incohérence HT + TVA ≠ TTC")

    risk = []
    if inv["amount_ttc"] is not None and inv["amount_ttc"] > 2000:
        risk.append("Montant élevé")
    if inv["category"].lower() in ["deplacements","déplacements"] and inv["amount_ttc"] and inv["amount_ttc"] > 1000:
        risk.append("Dépense déplacement élevée")

    status = "À vérifier" if issues else "Prête à valider"
    risk_flag = ", ".join(risk) if risk else "RAS"
    return status, risk_flag, issues

def save_invoice(conn, inv, status, risk_flag):
    conn.execute("""
        INSERT INTO invoices
        (filename,supplier,invoice_date,invoice_number,amount_ht,vat,amount_ttc,category,object_text,status,risk_flag,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        inv["filename"],inv["supplier"],inv["invoice_date"],inv["invoice_number"],
        inv["amount_ht"],inv["vat"],inv["amount_ttc"],inv["category"],inv["object_text"],
        status,risk_flag,datetime.now().isoformat(timespec="seconds")
    ))
    conn.commit()

def load_all(conn):
    return pd.read_sql_query("SELECT * FROM invoices ORDER BY id DESC", conn)

def get_secret(name):
    try:
        return st.secrets.get(name, None)
    except Exception:
        return None

def llm_summary(inv, issues, risk_flag):
    api_key = os.getenv("OPENAI_API_KEY") or get_secret("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = f"""Tu es un assistant de gestion.
Analyse cette facture extraite et produis un résumé opérationnel de 4 lignes maximum.
Mentionne les éventuelles anomalies ou risques.

Facture:
{inv}

Erreurs:
{issues}

Risque:
{risk_flag}
"""
        resp = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resp.output_text
    except Exception:
        return None

conn = init_db()

with st.sidebar:
    st.header("Source du document")
    mode = st.radio("Choix", ["Document de démonstration", "Importer un fichier texte"])
    demo_choice = st.selectbox(
        "Facture de démonstration",
        ["invoice_alpha.txt","invoice_beta.txt","invoice_gamma.txt"]
    ) if mode == "Document de démonstration" else None
    uploaded = st.file_uploader("Importer un fichier .txt", type=["txt"]) if mode == "Importer un fichier texte" else None
    st.markdown("---")
    st.caption("Version portfolio légère. Une version production pourrait intégrer OCR, e-mail, ERP, API comptable et workflow d'approbation.")

if mode == "Document de démonstration":
    text = Path("sample_docs", demo_choice).read_text(encoding="utf-8")
    filename = demo_choice
elif uploaded is not None:
    text = uploaded.read().decode("utf-8", errors="ignore")
    filename = uploaded.name
else:
    st.info("Importez un document pour commencer.")
    st.stop()

inv = parse_invoice_text(text, filename)
status, risk_flag, issues = validate_invoice(inv)

tabs = st.tabs(["📄 Extraction", "✅ Contrôles", "🧠 Analyse IA", "📊 Suivi", "🏗 Architecture"])

with tabs[0]:
    st.subheader("Données extraites")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Fournisseur", value=inv["supplier"], disabled=True)
        st.text_input("Date", value=inv["invoice_date"], disabled=True)
        st.text_input("Numéro de facture", value=inv["invoice_number"], disabled=True)
        st.text_input("Catégorie", value=inv["category"], disabled=True)
    with c2:
        st.text_input("Montant HT", value=inv["amount_ht"], disabled=True)
        st.text_input("TVA", value=inv["vat"], disabled=True)
        st.text_input("Montant TTC", value=inv["amount_ttc"], disabled=True)
        st.text_input("Objet", value=inv["object_text"], disabled=True)

    if st.button("💾 Enregistrer dans le workflow", use_container_width=True):
        save_invoice(conn, inv, status, risk_flag)
        st.success("Facture enregistrée dans le workflow.")

with tabs[1]:
    st.subheader("Contrôles automatiques")
    a,b,c = st.columns(3)
    a.metric("Statut", status)
    b.metric("Risque", risk_flag)
    c.metric("Nb. contrôles en erreur", len(issues))

    if issues:
        for issue in issues:
            st.error(issue)
    else:
        st.success("Aucune incohérence bloquante détectée.")

    if risk_flag != "RAS":
        st.warning(f"Point de vigilance : {risk_flag}")

with tabs[2]:
    st.subheader("Analyse assistée")
    ai = llm_summary(inv, issues, risk_flag)
    if ai:
        st.success(ai)
    else:
        st.info("Mode démonstration sans clé API.")
        if issues:
            st.write(f"La facture nécessite une vérification car : {', '.join(issues)}.")
        elif risk_flag != "RAS":
            st.write(f"La facture est structurellement correcte mais présente un point de vigilance : {risk_flag}.")
        else:
            st.write(
                f"Facture de {inv['supplier']} d'un montant TTC de {inv['amount_ttc']} € "
                f"pour la catégorie {inv['category']}. Les contrôles de cohérence sont satisfaisants."
            )

with tabs[3]:
    st.subheader("Tableau de suivi")
    df = load_all(conn)
    if df.empty:
        st.info("Aucune facture enregistrée pour le moment.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Factures", len(df))
        c2.metric("Montant TTC cumulé", f"{df['amount_ttc'].fillna(0).sum():,.2f} €".replace(",", " "))
        c3.metric("À vérifier", int((df["status"]=="À vérifier").sum()))
        c4.metric("Avec risque", int((df["risk_flag"]!="RAS").sum()))
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger le suivi CSV", csv, "smartflow_invoices.csv", "text/csv")

with tabs[4]:
    st.subheader("Architecture du POC")
    st.code(
"""Document entrant
      ↓
Extraction structurée
      ↓
Contrôles métier
      ↓
Détection de risques
      ↓
Enregistrement SQL
      ↓
Validation humaine
      ↓
Dashboard de suivi
      ↓
API / ERP / e-mail en production""",
        language="text"
    )
    st.markdown("""
**Ce que démontre le projet :**
- compréhension d'un processus métier ;
- extraction de données ;
- contrôles automatisés ;
- stockage SQL ;
- validation humaine ;
- dashboard opérationnel ;
- intégration LLM optionnelle ;
- logique POC → solution exploitable.
""")

st.markdown("---")
st.caption("Projet portfolio — Python · Streamlit · SQLite · automatisation · contrôles métier · OpenAI API optionnelle")
