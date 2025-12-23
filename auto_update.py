import os
import sys
from datetime import datetime
from src import download_data, download_afcon_data

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # Append to log file
    with open("update_log.txt", "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def main():
    log("=== DEBUT MISE A JOUR AUTOMATIQUE ===")
    
    try:
        # Update league data
        log("Telechargement des donnees des championnats...")
        download_data.download_data()
        log("Championnats: OK")
        
        # Update AFCON data
        log("Telechargement des donnees AFCON...")
        download_afcon_data.download_afcon_data()
        log("AFCON: OK")
        
        log("=== MISE A JOUR TERMINEE AVEC SUCCES ===")
        return 0
        
    except Exception as e:
        log(f"ERREUR: {str(e)}")
        log("=== MISE A JOUR ECHOUEE ===")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
