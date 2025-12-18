"""
Punto de entrada principal
"""

import os
import subprocess
import sys
from datetime import datetime

def main():
    print("=" * 50)
    print("🤖 BOT OJS UPLOADER - PUNTO DE ENTRADA")
    print("=" * 50)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")
    print("=" * 50)
    
    # Verificar si usar start.sh o app.py directamente
    if os.path.exists("start.sh"):
        print("🚀 Ejecutando start.sh...")
        os.system("chmod +x start.sh")
        os.system("./start.sh")
    else:
        print("🚀 Ejecutando app.py directamente...")
        os.system(f"python app.py")

if __name__ == "__main__":
    main()