#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Garmin Trainer - Applicazione per la gestione degli allenamenti su Garmin Connect

Questa applicazione consente di creare, modificare e pianificare allenamenti
per corsa, ciclismo e nuoto, e di caricarli su Garmin Connect.
"""

import sys
import os
import logging
from tkinter import Tk

# Aggiungi il percorso corrente al path Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("garmin_trainer.log")
    ]
)

from gui.app import GarminTrainerApp

def main():
    """Punto di ingresso principale dell'applicazione"""
    root = Tk()
    root.title("Garmin Trainer")
    
    # Dimensione finestra principale
    root.geometry("1100x700")
    
    # Inizializza l'applicazione
    app = GarminTrainerApp(root)
    
    # Avvia il loop principale
    root.mainloop()

if __name__ == "__main__":
    main()