
from .domain.BHXH import BHXH

def smart_chuck_domain(forder_path:str ,title: str) -> str: 
    domain = title
    folder_path = forder_path
    # print(domain,file_path)

    DOMAIN = {
        "BHXH" : lambda file_path: BHXH(folder_path)
    }

    if domain in DOMAIN:
        hander = DOMAIN[domain]
        return hander(folder_path)
    else:
        print(f"Domain {domain} không được hỗ trợ ")
        return ""