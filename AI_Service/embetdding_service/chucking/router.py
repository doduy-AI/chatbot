
from .domain.BHXH import BHXH

def smart_chuck_domain(forder_path:str ,title: str,u_id:str ,groupId: str , base: str) -> str: 
    domain = title
    folder_path = forder_path
    # print(domain,file_path)

    DOMAIN = {
        "BHXH" : lambda file_path: BHXH(file_path,u_id, groupId, base)
    }

    if domain in DOMAIN:
        hander = DOMAIN[domain]
        return hander(folder_path)
    else:
        print(f"Domain {domain} không được hỗ trợ ")
        return ""