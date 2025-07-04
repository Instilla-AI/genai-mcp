#!/usr/bin/env python3
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from google.cloud import bigquery
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BigQueryMCPServer:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'big-query-instilla')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            # Se abbiamo il JSON delle credenziali come variabile d'ambiente
            creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if creds_json:
                import tempfile
                import json
                
                # Scrivi temporaneamente le credenziali su file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(creds_json)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
            
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client inizializzato per il progetto: {self.project_id}")
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del client BigQuery: {e}")
            raise
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Gestisce le richieste MCP secondo il protocollo standard"""
        try:
            method = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')
            
            logger.info(f"Ricevuta richiesta MCP: {method}")
            
            if method == 'initialize':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'bigquery-mcp-server',
                            'version': '1.0.0'
                        }
                    }
                }
            
            elif method == 'tools/list':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'tools': [
                            {
                                'name': 'query_bigquery',
                                'description': 'Esegue una query SQL su BigQuery',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'query': {
                                            'type': 'string',
                                            'description': 'Query SQL da eseguire'
                                        },
                                        'limit': {
                                            'type': 'number',
                                            'description': 'Limite di righe da restituire (default: 100)',
                                            'default': 100
                                        }
                                    },
                                    'required': ['query']
                                }
                            },
                            {
                                'name': 'list_datasets',
                                'description': 'Lista tutti i dataset disponibili nel progetto',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {}
                                }
                            },
                            {
                                'name': 'list_tables',
                                'description': 'Lista le tabelle in un dataset',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'dataset_id': {
                                            'type': 'string',
                                            'description': 'ID del dataset'
                                        }
                                    },
                                    'required': ['dataset_id']
                                }
                            },
                            {
                                'name': 'describe_table',
                                'description': 'Descrive la struttura di una tabella',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'dataset_id': {
                                            'type': 'string',
                                            'description': 'ID del dataset'
                                        },
                                        'table_id': {
                                            'type': 'string',
                                            'description': 'ID della tabella'
                                        }
                                    },
                                    'required': ['dataset_id', 'table_id']
                                }
                            }
                        ]
                    }
                }
            
            elif method == 'tools/call':
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                result = await self.call_tool(tool_name, arguments)
                
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': result
                }
            
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Metodo non trovato: {method}'
                    }
                }
                
        except Exception as e:
            logger.error(f"Errore nella gestione della richiesta: {e}")
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': f'Errore interno del server: {str(e)}'
                }
            }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue uno strumento"""
        try:
            if name == 'query_bigquery':
                return await self.query_bigquery(arguments)
            elif name == 'list_datasets':
                return await self.list_datasets_impl()
            elif name == 'list_tables':
                return await self.list_tables(arguments)
            elif name == 'describe_table':
                return await self.describe_table(arguments)
            else:
                raise ValueError(f'Strumento non trovato: {name}')
                
        except Exception as e:
            logger.error(f"Errore nell'esecuzione dello strumento {name}: {e}")
            raise
    
    async def query_bigquery(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue una query BigQuery"""
        query = args.get('query', '')
        limit = args.get('limit', 100)
        
        try:
            if 'LIMIT' not in query.upper() and limit:
                query = f"{query} LIMIT {limit}"
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            rows = []
            for row in results:
                rows.append(dict(row))
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Query eseguita con successo. Righe restituite: {len(rows)}\n\nRisultati:\n{json.dumps(rows, indent=2, default=str)}"
                    }
                ]
            }
        except Exception as e:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Errore nell'esecuzione della query: {str(e)}"
                    }
                ]
            }
    
    async def list_datasets_impl(self) -> Dict[str, Any]:
        """Lista i dataset"""
        try:
            datasets = list(self.client.list_datasets())
            dataset_info = []
            
            for dataset in datasets:
                try:
                    full_dataset = self.client.get_dataset(dataset.dataset_id)
                    dataset_info.append({
                        'dataset_id': dataset.dataset_id,
                        'project': dataset.project,
                        'location': full_dataset.location,
                        'created': str(full_dataset.created) if full_dataset.created else None,
                        'description': full_dataset.description or 'Nessuna descrizione',
                        'labels': dict(full_dataset.labels) if full_dataset.labels else {}
                    })
                except Exception as e:
                    dataset_info.append({
                        'dataset_id': dataset.dataset_id,
                        'project': dataset.project,
                        'full_name': f"{dataset.project}.{dataset.dataset_id}",
                        'error': f'Impossibile ottenere dettagli: {str(e)}'
                    })
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Dataset trovati: {len(dataset_info)}\n\n{json.dumps(dataset_info, indent=2)}"
                    }
                ]
            }
        except Exception as e:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Errore nel recuperare i dataset: {str(e)}"
                    }
                ]
            }
    
    async def list_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Lista le tabelle in un dataset"""
        dataset_id = args.get('dataset_id')
        
        try:
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            table_info = []
            for table in tables:
                table_data = {
                    'table_id': table.table_id,
                    'table_type': table.table_type,
                    'full_name': f"{table.project}.{table.dataset_id}.{table.table_id}"
                }
                
                try:
                    if hasattr(table, 'created') and table.created:
                        table_data['created'] = str(table.created)
                    if hasattr(table, 'num_rows') and table.num_rows is not None:
                        table_data['num_rows'] = table.num_rows
                except:
                    pass
                
                table_info.append(table_data)
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Tabelle nel dataset {dataset_id}: {len(table_info)}\n\n{json.dumps(table_info, indent=2)}"
                    }
                ]
            }
        except Exception as e:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Errore nel recuperare le tabelle: {str(e)}"
                    }
                ]
            }
    
    async def describe_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Descrive una tabella"""
        dataset_id = args.get('dataset_id')
        table_id = args.get('table_id')
        
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            table = self.client.get_table(table_ref)
            
            schema_info = []
            for field in table.schema:
                schema_info.append({
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description or 'Nessuna descrizione'
                })
            
            table_info = {
                'table_id': table.table_id,
                'dataset_id': table.dataset_id,
                'project': table.project,
                'num_rows': table.num_rows,
                'schema': schema_info,
                'created': str(table.created) if table.created else None,
                'modified': str(table.modified) if table.modified else None,
                'description': table.description or 'Nessuna descrizione'
            }
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Descrizione tabella {dataset_id}.{table_id}:\n\n{json.dumps(table_info, indent=2)}"
                    }
                ]
            }
        except Exception as e:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Errore nel descrivere la tabella: {str(e)}"
                    }
                ]
            }

# Inizializza FastAPI
app = FastAPI(title="BigQuery MCP Server", version="1.0.0")

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializza il server BigQuery
mcp_server = BigQueryMCPServer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'BigQuery MCP Server with SSE',
        'project': mcp_server.project_id,
        'protocol': 'MCP over SSE'
    }

@app.get("/")
async def root():
    """Root endpoint con informazioni del server"""
    return {
        'name': 'BigQuery MCP Server',
        'version': '1.0.0',
        'protocol': 'MCP over SSE',
        'project': mcp_server.project_id,
        'endpoints': {
            'health': '/health',
            'sse': '/sse',
            'tools': 'Use MCP client to connect via SSE'
        },
        'usage': 'Connect using MCP Client with SSE transport'
    }

@app.post("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint per il protocollo MCP"""
    
    async def event_stream():
        try:
            # Legge il corpo della richiesta
            body = await request.body()
            if body:
                mcp_request = json.loads(body.decode('utf-8'))
                
                # Processa la richiesta MCP
                response = await mcp_server.handle_mcp_request(mcp_request)
                
                # Formatta come evento SSE
                yield f"data: {json.dumps(response)}\n\n"
            else:
                # Connessione keep-alive
                yield f"data: {json.dumps({'type': 'connected'})}\n\n"
                
        except Exception as e:
            logger.error(f"Errore nel flusso SSE: {e}")
            error_response = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32603,
                    'message': f'Errore del server SSE: {str(e)}'
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
