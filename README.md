# GenAI MCP - BigQuery Natural Language Interface

Sistema MCP (Model Context Protocol) per convertire linguaggio naturale in query BigQuery per analisi di vendite.

## 🚀 Funzionalità

- **Natural Language to SQL**: Converte richieste italiane in query BigQuery
- **Schema Discovery**: Esplora automaticamente dataset e tabelle
- **Query Predefinite**: Template ottimizzati per analisi vendite
- **Dashboard Metriche**: KPI aggregati in tempo reale
- **Deploy Railway**: Configurazione pronta per il cloud

## 📊 Schema Dati

### Tabella: `vendite_dataset.vendite`

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| `id` | INT64 | ID univoco vendita |
| `data_vendita` | DATE | Data vendita |
| `prodotto` | STRING | Nome prodotto |
| `quantita` | INT64 | Quantità venduta |
| `prezzo_unitario` | FLOAT64 | Prezzo unitario €  |
| `totale` | FLOAT64 | Totale vendita € |
| `cliente` | STRING | Nome cliente |
| `regione` | STRING | Regione (Nord/Sud/Centro) |

## 🔧 Setup Locale

1. **Prerequisiti**:
   ```bash
   # Google Cloud SDK
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
