# backend/update_all_tokens.py

import time
from services.ghl_client import refresh_agency_token, get_installed_locations, manage_location_tokens

if __name__ == "__main__":
    print(f"=== Iniciando Update Completo de Tokens ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")

    # 1) Atualiza o token da agência
    if not refresh_agency_token():
        print("\n>>> FALHA no refresh do token da agência. Verifique os logs acima.")
        exit(1)
    else:
        print("\n>>> [update_all_tokens] Token da agência atualizado com sucesso.\n")

    # 2) Busca e salva as installed locations
    if not get_installed_locations():
        print("\n>>> FALHA ao obter installed locations. Verifique os logs acima.")
        exit(1)
    else:
        print("\n>>> [update_all_tokens] Installed locations obtidas com sucesso.\n")

    # 3) Para cada installed location, obtém o token e salva no JSON
    if not manage_location_tokens():
        print("\n>>> FALHA ao obter tokens de location. Verifique os logs acima.")
        exit(1)
    else:
        print("\n>>> [update_all_tokens] Tokens de todas as locations obtidos com sucesso.\n")

    print("=== update_all_tokens.py concluído com sucesso! ===")
