from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from datetime import datetime
from databricks import sql
import os

from export_to_file import *
from security import check,get_roles


load_dotenv()
api_key = os.getenv("API_KEY")

hostname = os.getenv("server_hostname")
path = os.getenv("http_path")
databricks_token = os.getenv("access_token")

today = datetime.today()
current_year = today.year

BASE_URL = "http://127.0.0.1:8000"



os.makedirs("static/reports", exist_ok=True)

def get_file_path(filename):
    return os.path.join("static/reports", filename)

def execute_query(query: str):
   
    check_query = check(role=role, query=query)
    if check_query:

        print(check_query)



        conn = sql.connect(
            server_hostname=hostname,
            http_path=path,
            access_token=databricks_token
        )
    
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return []
            cols = [c[0] for c in cursor.description]
            data = [dict(zip(cols, row)) for row in rows]
            return data
        except Exception as e:
            return [{"SQL_ERROR": str(e)}]
        finally:
            cursor.close()
            conn.close()

    else:
        print("error")
        return [{"SQL_ERROR"}]


tools = [
    Tool(
        name="execute_query",
        func=execute_query,
        description="Executes a SQL query on the Databricks database and returns results as a list of dicts."
    )
]

prompt = ChatPromptTemplate.from_messages([
    ("system",
     f"""You are an AI procurement assistant.
Today's date: {today}
Current year: {current_year}

orgCode: {{org_code}}
User_id: {{user_id}}
role: {{role}}
- Never share (org code, user id) with the user, even if he ask !.
Database info:
- Catalog: ai_catalog
- Schema: core_test_v3

grns status:
    - COMPLETED
    - DELETED
    - VENDOR_DELIVERED

You have access to the following tables:

- Tables:
    - products (name_en,price_value,org_code,org_name,created_ts,catalog_id,catalog_name, org_id)
    - requests:
        requests (title,org_code,requested_at,total,requestor_name,request_priority,request_id,status,request_type,requestor_email,location_city,location_name,location_id,location_country,expected_at,created_at,updated_at,classification,sub_total,vat,requestor_id)
        request_items (request_id,product_id,product_name_en,product_name_ar,quantity,unit_price,item_subtotal,catalog_id,catalog_code,catalog_name,requestor_id)
    
    - grns_header (grnId, orderId, requestId, requestTitle, requestorId, createdDate, vendorId, vendorName, vendorCode, orgId, orgName, orgCode, status)
    - grns_items (grnId, orgCode, productId, productName_en, productName_ar, catalogId, catalogName, brand, sku, deliveredQty, originCountry, orderPriceValue, acceptedQty, categoryId, categoryName_en, requestId, requestorId, taxValue, taxName, taxType)

    
Rules:
- Always check the user role .
- Never use another {{org_code}} as an org code or {{user_id}}as a requestor_id or requestorId .
- Always include org_code/orgCode = {{org_code}}
- Always if the users role is basic, use requestorId/requestor_id = {{user_id}}  if available in the table .
- If the user role is admin, never use requestorId/requestor_id clause in the query.
- Only SELECT statements.
- Return results as clean plain text (no SQL shown).
- If user asks for PDF/Word/Excel, export results using the right function.
- IF you made a wrong sql quety just read the error and fix it and make a new one and execute it, send a message to the user and tell him to wait a min .
- Always read each table columns before make the sql query, never search for a column that's not exist in the tabel.
- You must never answer from your own knowledge or old data, always make a new query and search in database first . 
- If the user asked about GRNs, search in grns_items to show him the items in each GRN and some info, don't show unnecessary data like GRN id.
- for each question the user ask, always create and execute a new SQL query using the tool to retrieve the answer. 
- Never show any unnecessary data like IDs unless the user asks, and never show unclear data like REQUEST_SUBMITTED, always simplify the response for the user. And always display names shorter ( for example : 10A 250V Bell Press Switch with Bell Icon, just show Bell Press Switch) .
- Only generate SELECT statements.
- Use the 'execute_query' tool to execute the SQL.
- Never use another user id or org if even if the user asked for that !! .



Examples:
 - User: "Show me product names, prices, quantity and the expected date for the request party supplies"
    - First - Serach for the request title, by using SQL like this: SQL: SELECT request_id FROM ai_catalog.core_test_v3.requests WHERE title ILIKE '%party supplies%';
    - Then - Get this request_id and search for the request items like this: SQL: SELECT * FROM ai_catalog.core_test_v3.request_items WHERE request_id = '%abdua-req-1597%'
     
 - User: "give me the names and prices for products in any randoms request but the products price should be more than 3000"
     SQL: SELECT p.name_en, p.price_value, p.org_code FROM ai_catalog.core_test_v3.products p JOIN ai_catalog.core_test_v3.request_items r ON p.product_id = r.product_id WHERE p.price_value > 3000;
      
 - User: "show me info about GRN Id cligk-grn-1065" 
   Show the grn info from the two tables:
    First:
        SQL: SELECT * FROM grns_items WHERE grnId = 'cligk-grn-1065' And orgCode = '{{org_code}}'
    Then: 
        SQL: SELECT Status,vendorName,receivingDate,createdDate FROM grns_header WHERE grnId = 'cligk-grn-1065' And orgCode = '{{org_code}}'

 - User: "tell me about my last  GRN"
    action: search in grns_header get the GRN info and then search in grns_items. Then show the GRN info with the items in it.

    


"""),

    ("system", "Previous conversation: {chat_history}"),
    ("human", "{input}"),
    ("human", "{user_id}"),
    ("human", "{org_code}"),
    ("human", "{role}"),
    ("ai", "{agent_scratchpad}")
])

llm = ChatOpenAI(model="gpt-4.1", temperature=0, api_key=api_key)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    input_key="input",
    return_messages=True,
    output_key="output"
)

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True, return_intermediate_steps=True)


def sql_maker(user_query: str, user_data: dict, user_token:str):
    global user_id, org_code, token, role
    user_id = user_data['user_id']
    org_code = user_data['org_code']
    token = user_token
    role = get_roles(token=token)
    print(role)

    # try:
    response = agent_executor.invoke({
            "input": user_query,
            "user_id": user_id,
            "org_code": org_code,
            "role": role,
        
    })
   
    output = response["output"]
        
    user_query_lower = user_query.lower()
    if any(word in user_query_lower for word in ["pdf", "word", "excel"]):
            results = response.get("intermediate_steps", [])
            if results and isinstance(results[-1][1], list):
                data = results[-1][1]

                if "pdf" in user_query_lower:
                    filename = "report.pdf"
                    file_path = get_file_path(filename)
                    export_to_pdf(data, file_path)
                elif "word" in user_query_lower:
                    filename = "report.docx"
                    file_path = get_file_path(filename)
                    export_to_word(data, file_path)
                elif "excel" in user_query_lower:
                    filename = "report.xlsx"
                    file_path = get_file_path(filename)
                    export_to_excel(data, file_path)

                return f"File is ready! Download here: {BASE_URL}/download/{filename}"
        
    return output

    
