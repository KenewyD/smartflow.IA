# SmartFlow AI

Automatisation intelligente d'un processus de gestion de factures.

## Démo

Après déploiement, remplacez le lien ci-dessous :

🔗 **Tester l'application :** ## Démo

🔗 [Tester l'application en ligne](https://smartflowia-rv42xc7hxrtaz9ejueefes.streamlit.app/)`

## Problème métier

Les équipes de gestion traitent encore de nombreuses factures et pièces administratives manuellement :
- lecture du document ;
- extraction des informations ;
- contrôle des montants ;
- détection d'erreurs ;
- saisie dans un outil ;
- validation ;
- reporting.

SmartFlow AI automatise ces étapes dans un POC simple et testable.

## Fonctionnalités

- lecture d'une facture texte ;
- extraction automatique des champs ;
- contrôle HT / TVA / TTC ;
- détection de données manquantes ;
- détection de risques simples ;
- workflow de validation ;
- enregistrement SQLite ;
- tableau de suivi ;
- export CSV ;
- résumé LLM optionnel.

## Workflow

```text
Document entrant
      ↓
Extraction structurée
      ↓
Contrôles métier
      ↓
Détection de risques
      ↓
Base SQL
      ↓
Validation humaine
      ↓
Dashboard
```

## Stack

Python, Streamlit, SQLite, Pandas, OpenAI API.

## Pourquoi ce projet ?

Ce projet illustre le passage d'un besoin métier à une application exploitable :
- analyse du processus ;
- automatisation ;
- stockage ;
- contrôle ;
- interface utilisateur ;
- possibilité d'intégration avec ERP, e-mail, API ou outils comptables.

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Activer OpenAI

Dans Streamlit Community Cloud, ajouter :

```toml
OPENAI_API_KEY="votre_cle"
```

Ne jamais publier une clé API dans GitHub.

## Structure

```text
smartflow-ai/
├── app.py
├── sample_docs/
│   ├── invoice_alpha.txt
│   ├── invoice_beta.txt
│   └── invoice_gamma.txt
├── requirements.txt
├── README.md
└── .gitignore
```

## Extensions production possibles

- OCR PDF / image ;
- récupération automatique depuis une boîte e-mail ;
- connexion ERP ;
- FastAPI ;
- PostgreSQL ;
- file d'approbation ;
- authentification ;
- journal d'audit ;
- notifications.

## Auteur

Khadidiatou Kenewy Diallo
