#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Definizione degli stili e dei colori utilizzati nell'interfaccia grafica.
"""

import tkinter as tk
from tkinter import ttk

# Colori principali
COLORS = {
    "primary": "#1976D2",     # Blu primario
    "primary_dark": "#0D47A1", # Blu scuro
    "primary_light": "#64B5F6", # Blu chiaro
    "accent": "#FF4081",       # Rosa accent
    "text_light": "#FFFFFF",   # Testo su sfondo scuro
    "text_dark": "#212121",    # Testo su sfondo chiaro
    "bg_light": "#F5F5F5",     # Sfondo chiaro
    "bg_dark": "#424242",      # Sfondo scuro
    "success": "#4CAF50",      # Verde successo
    "warning": "#FFC107",      # Giallo avviso
    "error": "#F44336",        # Rosso errore
    "info": "#2196F3",         # Blu info
    
    # Colori per i tipi di passo
    "warmup": "#FFA726",       # Arancione per il riscaldamento
    "cooldown": "#81C784",     # Verde chiaro per il defaticamento
    "interval": "#EF5350",     # Rosso per gli intervalli
    "recovery": "#9FA8DA",     # Viola chiaro per il recupero
    "rest": "#B0BEC5",         # Grigio per il riposo
    "repeat": "#7986CB",       # Blu-viola per le ripetizioni
    "other": "#90A4AE",        # Grigio-blu per altri tipi
    
    # Colori per i tipi di sport
    "running": "#FF7043",      # Arancione-rosso per la corsa
    "cycling": "#66BB6A",      # Verde per il ciclismo
    "swimming": "#29B6F6",     # Azzurro per il nuoto
    "strength_training": "#AB47BC", # Viola per l'allenamento di forza
    "cardio": "#F44336",       # Rosso per il cardio
    "flexibility_training": "#9575CD", # Viola chiaro per la flessibilità
    "other_sport": "#78909C"   # Grigio-blu per altri sport
}

# Icone per i tipi di passo
STEP_ICONS = {
    "warmup": "🔥",       # Riscaldamento
    "cooldown": "❄️",     # Defaticamento
    "interval": "⚡",      # Intervallo
    "recovery": "🌊",     # Recupero
    "rest": "⏸️",         # Riposo
    "repeat": "🔄",       # Ripetizione
    "other": "📝"         # Altro
}

# Icone per i tipi di sport
SPORT_ICONS = {
    "running": "🏃",          # Corsa
    "cycling": "🚴",          # Ciclismo
    "swimming": "🏊",         # Nuoto
    "strength_training": "🏋️", # Allenamento forza
    "cardio": "❤️",           # Cardio
    "flexibility_training": "🧘", # Flessibilità
    "other": "🏅"             # Altro sport
}

def setup_styles():
    """Configura gli stili per i widget ttk"""
    style = ttk.Style()
    
    # Tema di base (scegliamo clam che è più personalizzabile)
    style.theme_use('clam')
    
    # Stile generale dei pulsanti
    style.configure(
        'TButton',
        background=COLORS["primary"],
        foreground=COLORS["text_light"],
        padding=(10, 5),
        font=('Arial', 10)
    )
    
    # Pulsante di successo (verde)
    style.configure(
        'Success.TButton',
        background=COLORS["success"],
        foreground=COLORS["text_light"]
    )
    
    # Pulsante di pericolo (rosso)
    style.configure(
        'Danger.TButton',
        background=COLORS["error"],
        foreground=COLORS["text_light"]
    )
    
    # Pulsante info (blu chiaro)
    style.configure(
        'Info.TButton',
        background=COLORS["info"],
        foreground=COLORS["text_light"]
    )
    
    # Pulsante piccolo
    style.configure(
        'Small.TButton',
        padding=(5, 2),
        font=('Arial', 9)
    )
    
    # Etichette per i titoli
    style.configure(
        'Heading.TLabel',
        font=('Arial', 14, 'bold'),
        foreground=COLORS["primary_dark"]
    )
    
    # Etichette per i sottotitoli
    style.configure(
        'Subheading.TLabel',
        font=('Arial', 12, 'bold'),
        foreground=COLORS["primary"]
    )
    
    # Etichette per le istruzioni
    style.configure(
        'Instructions.TLabel',
        font=('Arial', 10, 'italic'),
        foreground=COLORS["text_dark"]
    )
    
    # Etichette per lo stato
    style.configure(
        'Status.TLabel',
        font=('Arial', 9),
        foreground=COLORS["primary_dark"]
    )
    
    # Frame per i contenitori principali
    style.configure(
        'Main.TFrame',
        background=COLORS["bg_light"]
    )
    
    # Frame per i contenitori secondari
    style.configure(
        'Secondary.TFrame',
        background=COLORS["bg_light"],
        borderwidth=1,
        relief='groove'
    )
    
    # Stile per i notebook (tab)
    style.configure(
        'TNotebook',
        background=COLORS["bg_light"],
        tabmargins=[2, 5, 2, 0]
    )
    
    style.configure(
        'TNotebook.Tab',
        background=COLORS["primary_light"],
        foreground=COLORS["text_dark"],
        padding=[10, 2],
        font=('Arial', 10)
    )
    
    style.map(
        'TNotebook.Tab',
        background=[('selected', COLORS["primary"])],
        foreground=[('selected', COLORS["text_light"])],
        expand=[('selected', [1, 1, 1, 0])]
    )