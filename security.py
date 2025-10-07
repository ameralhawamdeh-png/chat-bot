import re
import requests

url = "https://api-test.penny.co/api/auth/package"







def get_roles(token:str):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()  

    grn_roles = []

    def get_user_role(obj):
        if isinstance(obj, dict):
            if "userPackage" in obj:
                user_package = obj["userPackage"]
                if "userProfileDetail" in user_package:
                    roles = user_package["userProfileDetail"].get("roles", [])
                    for role in roles:
                        grn_roles.append(role['code'])

            for v in obj.values():
                get_user_role(v)
        elif isinstance(obj, list):
            for item in obj:
                get_user_role(item)


    get_user_role(data)

    if "grn_workspace_admin" in grn_roles:

        role = "admin"

    else:
        if "grn_super_admin" in grn_roles:
            role = "admin"
        else:
            role = "basic"

    return role










def check(role:str, query:str)->bool:

    """
    Check if a SQL query contains a WHERE clause with both:
      - An org_code/orgCode filter
      - A user_id/requestor_id/requestorId filter
    Returns True if valid, False otherwise.
    """
    normalized = query.lower()

    message = ""

    if "where" not in normalized:  
        message = "Query missing WHERE clause"
        print(message)
        return False
    
    where_part = normalized.split("where", 1)[1]

    # Possible column name
    org_fields = ["org_code", "orgcode"]
    user_fields = ["user_id", "userid", "requestor_id", "requestorid"]

    # Check if any of these appear in the WHERE clause
    has_org_condition = any(re.search(rf"\b{col}\b", where_part) for col in org_fields)
    has_user_condition = any(re.search(rf"\b{col}\b", where_part) for col in user_fields)
    

    # role = get_roles(token)
    

    if role == "basic":


       

        if not has_org_condition:
            message = "Missing organization filter (org_code/orgCode)"
            print(message)
        if not has_user_condition:
            message = "Missing user filter (user_id/requestorId/etc.)"
            print(message)

        return has_org_condition and has_user_condition

    else:

        has_org_condition = any(re.search(rf"\b{col}\b", where_part) for col in org_fields)

        if not has_org_condition:
            message = "Missing organization filter (org_code/orgCode)"
            print(message)
    

        return has_org_condition 
    
    
    



    

    
