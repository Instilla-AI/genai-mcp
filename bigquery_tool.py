def bigquery_tool(query: str):
    from langchain_google_genai import ChatGoogleGenerativeAI
    from toolbox.tools.bigquery import BigQueryNL2SQLTool

    tool = BigQueryNL2SQLTool(project_id="hip-nuova-folati")
    return tool.run(query)
