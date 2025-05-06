#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per la creazione e modifica di passi dell'allenamento.
"""

import tkinter as tk
from tkinter import ttk
import re

from core.workout import STEP_TYPES


class StepDialog:
    """Dialog per creare o modificare passi dell'allenamento."""
    
    def __init__(self, parent, step_type=None, step_detail=None, sport_type="running"):
        """
        Inizializza il dialog.
        
        Args:
            parent: Widget genitore
            step_type: Tipo di passo preselezionato (opzionale)
            step_detail: Dettagli del passo preselezionati (opzionale)
            sport_type: Tipo di sport per adattare le opzioni
        """
        self.parent = parent
        self.step_type = step_type
        self.step_detail = step_detail
        self.sport_type = sport_type
        self.result = None
        
        # Crea il dialog
        self.create_dialog()
    
    def create_dialog(self):
        """Crea il dialog."""
        # Finestra top-level
        self.top = tk.Toplevel(self.parent)
        self.top.title("Passo allenamento")
        self.top.geometry("500x450")
        self.top.transient(self.parent)
        self.top.grab_set()
        
        # Imposta lo stato modale
        self.top.focus_set()
        
        # Frame principale con padding
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        if self.step_type:
            title_text = f"Modifica passo: {self.step_type}"
        else:
            title_text = "Nuovo passo"
            
        title_label = ttk.Label(
            main_frame, 
            text=title_text, 
            style="Heading.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Frame per i controlli
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. Tipo di passo
        step_type_frame = ttk.Frame(form_frame)
        step_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(step_type_frame, text="Tipo di passo:").pack(side=tk.LEFT)
        
        # Lista di tipi di passo (escludi 'repeat' che viene gestito separatamente)
        step_types = ["warmup", "cooldown", "interval", "recovery", "rest", "other"]
        
        self.step_type_var = tk.StringVar(
            value=self.step_type if self.step_type in step_types else "interval"
        )
        
        step_type_combo = ttk.Combobox(
            step_type_frame, 
            textvariable=self.step_type_var,
            values=step_types,
            width=20,
            state="readonly"
        )
        step_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Associa evento di cambio
        step_type_combo.bind("<<ComboboxSelected>>", self.on_step_type_change)
        
        # 2. Condizione di fine
        end_condition_frame = ttk.Frame(form_frame)
        end_condition_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(end_condition_frame, text="Condizione di fine:").pack(side=tk.LEFT)
        
        # Opzioni di condizione di fine
        end_conditions = ["lap.button", "time", "distance"]
        self.end_condition_var = tk.StringVar(value=self.get_end_condition())
        
        end_condition_combo = ttk.Combobox(
            end_condition_frame, 
            textvariable=self.end_condition_var,
            values=end_conditions,
            width=20,
            state="readonly"
        )
        end_condition_combo.pack(side=tk.LEFT, padx=5)
        
        # Associa evento di cambio
        end_condition_combo.bind("<<ComboboxSelected>>", self.on_end_condition_change)
        
        # 3. Valore della condizione di fine
        self.end_value_frame = ttk.Frame(form_frame)
        self.end_value_frame.pack(fill=tk.X, pady=5)
        
        self.end_value_label = ttk.Label(self.end_value_frame, text="Valore:")
        self.end_value_label.pack(side=tk.LEFT)
        
        self.end_value_var = tk.StringVar(value=self.get_end_value())
        self.end_value_entry = ttk.Entry(self.end_value_frame, textvariable=self.end_value_var, width=15)
        self.end_value_entry.pack(side=tk.LEFT, padx=5)
        
        # 4. Target
        target_frame = ttk.Frame(form_frame)
        target_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        
        # Opzioni di target dipendenti dal tipo di sport
        target_options = self.get_target_options()
        
        self.target_var = tk.StringVar(value=self.get_target_type())
        
        target_combo = ttk.Combobox(
            target_frame, 
            textvariable=self.target_var,
            values=target_options,
            width=20,
            state="readonly"
        )
        target_combo.pack(side=tk.LEFT, padx=5)
        
        # Associa evento di cambio
        target_combo.bind("<<ComboboxSelected>>", self.on_target_change)
        
        # 5. Valori del target
        self.target_value_frame = ttk.Frame(form_frame)
        self.target_value_frame.pack(fill=tk.X, pady=5)
        
        # I contenuti di questo frame saranno aggiornati in base al tipo di target
        
        # 6. Descrizione
        description_frame = ttk.Frame(form_frame)
        description_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(description_frame, text="Descrizione:").pack(side=tk.LEFT)
        
        self.description_var = tk.StringVar(value=self.get_description())
        description_entry = ttk.Entry(description_frame, textvariable=self.description_var, width=30)
        description_entry.pack(side=tk.LEFT, padx=5)
        
        # 7. Anteprima finale
        preview_frame = ttk.LabelFrame(form_frame, text="Anteprima")
        preview_frame.pack(fill=tk.X, pady=5)
        
        self.preview_var = tk.StringVar()
        preview_label = ttk.Label(preview_frame, textvariable=self.preview_var, padding=10)
        preview_label.pack(fill=tk.X)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Salva", 
            command=self.on_save,
            style="Success.TButton",
            width=10
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Annulla", 
            command=self.on_cancel,
            width=10
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Inizializza i contenuti dinamici
        self.on_step_type_change()
        self.on_end_condition_change()
        self.on_target_change()
        self.update_preview()
        
        # Binding per aggiornare l'anteprima quando cambiano i valori
        self.end_value_var.trace_add("write", lambda *args: self.update_preview())
        self.description_var.trace_add("write", lambda *args: self.update_preview())
        
        # Attendi che il dialog sia completato
        self.top.wait_window()
    
    def get_target_options(self):
        """
        Restituisce le opzioni di target per il tipo di sport corrente.
        
        Returns:
            list: Opzioni di target
        """
        options = ["no.target"]
        
        if self.sport_type == "running":
            options.extend(["pace.zone", "heart.rate.zone"])
        elif self.sport_type == "cycling":
            options.extend(["power.zone", "speed.zone", "heart.rate.zone", "cadence.zone"])
        elif self.sport_type == "swimming":
            options.extend(["pace.zone", "heart.rate.zone"])
        else:
            options.extend(["heart.rate.zone"])
                
        return options

    def get_description(self):
        """
        Estrae la descrizione dal dettaglio del passo.
        
        Returns:
            str: Descrizione
        """
        if not self.step_detail:
            return ""
                
        if ' -- ' in self.step_detail:
            return self.step_detail.split(' -- ')[1].strip()
                
        return ""

    def on_save(self):
        """Salva le modifiche al passo."""
        try:
            # Validazione dei dati
            step_type = self.step_type_var.get()
            
            # Costruisci il dettaglio del passo
            detail = ""
            
            # Condizione di fine
            end_condition = self.end_condition_var.get()
            if end_condition == "lap.button":
                detail = "lap-button"
            else:
                detail = self.end_value_var.get()
            
            # Target
            target_type = self.target_var.get()
            if target_type != "no.target":
                target_value = getattr(self, 'target_value_var', tk.StringVar()).get()
                
                if target_type == "pace.zone":
                    detail += f" @ {target_value}"
                elif target_type == "heart.rate.zone":
                    detail += f" @hr {target_value}"
                elif target_type == "power.zone":
                    detail += f" @pwr {target_value}"
                elif target_type == "speed.zone":
                    detail += f" @spd {target_value}"
                elif target_type == "cadence.zone":
                    detail += f" @cad {target_value}"
            
            # Descrizione
            description = self.description_var.get().strip()
            if description:
                detail += f" -- {description}"
            
            # Imposta il risultato
            self.result = (step_type, detail)
            
            # Chiudi il dialog
            self.top.destroy()
            
        except Exception as e:
            # Mostra errore
            tk.messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il salvataggio: {str(e)}", 
                parent=self.top
            )


    def on_cancel(self):
        """Annulla le modifiche e chiude il dialog."""
        self.result = None
        self.top.destroy()

    def on_target_change(self, event=None):
        """
        Gestisce il cambio di tipo di target.
        
        Args:
            event: Evento di cambio (opzionale)
        """
        target_type = self.target_var.get()
        
        # Rimuovi i widget esistenti
        for widget in self.target_value_frame.winfo_children():
            widget.destroy()
        
        if target_type == "no.target":
            # Nessun input aggiuntivo richiesto
            pass
        
        elif target_type == "pace.zone":
            # Input per il ritmo
            ttk.Label(self.target_value_frame, text="Ritmo:").pack(side=tk.LEFT)
            
            # Ottieni i ritmi predefiniti dalla configurazione
            pace_options = self._get_config_paces()
            
            self.target_value_var = tk.StringVar(value=self.get_target_value() or pace_options[0] if pace_options else "5:00")
            
            target_combo = ttk.Combobox(
                self.target_value_frame, 
                textvariable=self.target_value_var,
                values=pace_options,
                width=15
            )
            target_combo.pack(side=tk.LEFT, padx=5)
            
            # Binding per aggiornare l'anteprima
            self.target_value_var.trace_add("write", lambda *args: self.update_preview())
        
        elif target_type == "heart.rate.zone":
            # Input per la zona di frequenza cardiaca
            ttk.Label(self.target_value_frame, text="Zona FC:").pack(side=tk.LEFT)
            
            # Ottieni le zone di frequenza cardiaca predefinite dalla configurazione
            hr_options = self._get_config_heart_rates()
            
            self.target_value_var = tk.StringVar(value=self.get_target_value() or hr_options[0] if hr_options else "Z1_HR")
            
            target_combo = ttk.Combobox(
                self.target_value_frame, 
                textvariable=self.target_value_var,
                values=hr_options,
                width=15
            )
            target_combo.pack(side=tk.LEFT, padx=5)
            
            # Binding per aggiornare l'anteprima
            self.target_value_var.trace_add("write", lambda *args: self.update_preview())
        
        elif target_type == "power.zone":
            # Input per la zona di potenza
            ttk.Label(self.target_value_frame, text="Zona potenza:").pack(side=tk.LEFT)
            
            # Ottieni le zone di potenza predefinite dalla configurazione
            power_options = self._get_config_power_zones()
            
            self.target_value_var = tk.StringVar(value=self.get_target_value() or power_options[0] if power_options else "Z3")
            
            target_combo = ttk.Combobox(
                self.target_value_frame, 
                textvariable=self.target_value_var,
                values=power_options,
                width=15
            )
            target_combo.pack(side=tk.LEFT, padx=5)
            
            # Binding per aggiornare l'anteprima
            self.target_value_var.trace_add("write", lambda *args: self.update_preview())
        
        elif target_type == "speed.zone":
            # Input per la zona di velocità
            ttk.Label(self.target_value_frame, text="Zona velocità:").pack(side=tk.LEFT)
            
            # Opzioni per la velocità
            speed_options = ["20-25 km/h", "25-30 km/h", "30-35 km/h"]
            
            # Valore del target attuale o default
            self.target_value_var = tk.StringVar(value=self.get_target_value() or "25-30 km/h")
            
            target_combo = ttk.Combobox(
                self.target_value_frame, 
                textvariable=self.target_value_var,
                values=speed_options,
                width=15
            )
            target_combo.pack(side=tk.LEFT, padx=5)
            
            # Binding per aggiornare l'anteprima
            self.target_value_var.trace_add("write", lambda *args: self.update_preview())
        
        elif target_type == "cadence.zone":
            # Input per la zona di cadenza
            ttk.Label(self.target_value_frame, text="Cadenza:").pack(side=tk.LEFT)
            
            # Opzioni per la cadenza
            cadence_options = ["80-90 rpm", "90-100 rpm", "100-110 rpm"]
            
            # Valore del target attuale o default
            self.target_value_var = tk.StringVar(value=self.get_target_value() or "90-100 rpm")
            
            target_combo = ttk.Combobox(
                self.target_value_frame, 
                textvariable=self.target_value_var,
                values=cadence_options,
                width=15
            )
            target_combo.pack(side=tk.LEFT, padx=5)
            
            # Binding per aggiornare l'anteprima
            self.target_value_var.trace_add("write", lambda *args: self.update_preview())
        
        # Aggiorna l'anteprima
        self.update_preview()

    def get_target_type(self):
        """
        Estrae il tipo di target dal dettaglio del passo.
        
        Returns:
            str: Tipo di target
        """
        if not self.step_detail:
            return "no.target"
            
        detail = self.step_detail
        
        if ' @ ' in detail:
            return "pace.zone"
        elif ' @spd ' in detail:
            return "speed.zone"
        elif ' @hr ' in detail:
            return "heart.rate.zone"
        elif ' @pwr ' in detail:
            return "power.zone"
        elif ' @cad ' in detail:
            return "cadence.zone"
        
        return "no.target"

    def on_step_type_change(self, event=None):
        """
        Gestisce il cambio di tipo di passo.
        
        Args:
            event: Evento di cambio (opzionale)
        """
        step_type = self.step_type_var.get()
        
        # Imposta valori di default per ciascun tipo
        if step_type == "warmup":
            if not self.end_value_var.get():
                self.end_condition_var.set("time")
                self.end_value_var.set("10min")
            
            # Target di default per il riscaldamento
            if self.target_var.get() == "no.target" and self.sport_type == "running":
                self.target_var.set("heart.rate.zone")
                self.on_target_change()
        
        elif step_type == "cooldown":
            if not self.end_value_var.get():
                self.end_condition_var.set("time")
                self.end_value_var.set("5min")
            
            # Target di default per il defaticamento
            if self.target_var.get() == "no.target" and self.sport_type == "running":
                self.target_var.set("heart.rate.zone")
                self.on_target_change()
        
        elif step_type == "interval":
            if not self.end_value_var.get():
                self.end_condition_var.set("distance")
                self.end_value_var.set("400m")
            
            # Target di default per l'intervallo
            if self.target_var.get() == "no.target":
                if self.sport_type == "running":
                    self.target_var.set("pace.zone")
                elif self.sport_type == "cycling":
                    self.target_var.set("power.zone")
                elif self.sport_type == "swimming":
                    self.target_var.set("pace.zone")
                self.on_target_change()
        
        elif step_type == "recovery":
            if not self.end_value_var.get():
                self.end_condition_var.set("time")
                self.end_value_var.set("1min")
            
            # Target di default per il recupero
            if self.target_var.get() == "no.target" and self.sport_type == "running":
                self.target_var.set("heart.rate.zone")
                self.on_target_change()
        
        elif step_type == "rest":
            if not self.end_value_var.get():
                self.end_condition_var.set("time")
                self.end_value_var.set("30s")
        
        # Aggiorna l'anteprima
        self.update_preview()

    def on_end_condition_change(self, event=None):
        """
        Gestisce il cambio di condizione di fine.
        
        Args:
            event: Evento di cambio (opzionale)
        """
        end_condition = self.end_condition_var.get()
        
        if end_condition == "lap.button":
            self.end_value_label.config(text="Valore:")
            self.end_value_entry.config(state=tk.DISABLED)
            self.end_value_var.set("")
        
        elif end_condition == "time":
            self.end_value_label.config(text="Durata:")
            self.end_value_entry.config(state=tk.NORMAL)
            
            # Se il valore attuale non è compatibile con il tempo
            current_value = self.end_value_var.get()
            if not current_value or "km" in current_value or "m" in current_value and "min" not in current_value:
                self.end_value_var.set("1min")
        
        elif end_condition == "distance":
            self.end_value_label.config(text="Distanza:")
            self.end_value_entry.config(state=tk.NORMAL)
            
            # Se il valore attuale non è compatibile con la distanza
            current_value = self.end_value_var.get()
            if not current_value or "min" in current_value or "s" in current_value:
                self.end_value_var.set("400m")
        
        # Aggiorna l'anteprima
        self.update_preview()

    def get_end_condition(self):
        """
        Estrae la condizione di fine dal dettaglio del passo.
        
        Returns:
            str: Condizione di fine
        """
        if not self.step_detail:
            return "lap.button"
            
        # Rimuovi eventuali parti dopo " -- " (descrizione)
        detail = self.step_detail
        if ' -- ' in detail:
            detail = detail.split(' -- ')[0]
        
        # Rimuovi le parti di target
        if ' @ ' in detail:
            detail = detail.split(' @ ')[0]
        elif ' @spd ' in detail:
            detail = detail.split(' @spd ')[0]
        elif ' @hr ' in detail:
            detail = detail.split(' @hr ')[0]
        elif ' @pwr ' in detail:
            detail = detail.split(' @pwr ')[0]
        
        # Estrai la condizione di fine
        detail = detail.strip()
        
        if detail == "lap-button":
            return "lap.button"
        elif 'min' in detail or ':' in detail:
            return "time"
        elif 'km' in detail or 'm' in detail and 'min' not in detail:
            return "distance"
        
        return "lap.button"
    
    def get_end_value(self):
        """
        Estrae il valore della condizione di fine dal dettaglio del passo.
        
        Returns:
            str: Valore della condizione di fine
        """
        if not self.step_detail:
            return ""
            
        # Rimuovi eventuali parti dopo " -- " (descrizione)
        detail = self.step_detail
        if ' -- ' in detail:
            detail = detail.split(' -- ')[0]
        
        # Rimuovi le parti di target
        if ' @ ' in detail:
            detail = detail.split(' @ ')[0]
        elif ' @spd ' in detail:
            detail = detail.split(' @spd ')[0]
        elif ' @hr ' in detail:
            detail = detail.split(' @hr ')[0]
        elif ' @pwr ' in detail:
            detail = detail.split(' @pwr ')[0]
        
        # Estrai il valore
        detail = detail.strip()
        
        # Per distanza
        if 'km' in detail or 'm' in detail and 'min' not in detail:
            return detail
        # Per tempo
        elif 'min' in detail:
            return detail
        elif ':' in detail:
            return detail
        
        return ""
        
    def get_target_value(self):
        """
        Estrae il valore del target dal dettaglio del passo.
        
        Returns:
            str: Valore del target
        """
        if not self.step_detail:
            return ""
            
        detail = self.step_detail
        
        if ' @ ' in detail:
            parts = detail.split(' @ ')
            if len(parts) >= 2:
                # Rimuovi la descrizione, se presente
                target_value = parts[1]
                if ' -- ' in target_value:
                    target_value = target_value.split(' -- ')[0]
                return target_value.strip()
        
        elif ' @spd ' in detail:
            parts = detail.split(' @spd ')
            if len(parts) >= 2:
                # Rimuovi la descrizione, se presente
                target_value = parts[1]
                if ' -- ' in target_value:
                    target_value = target_value.split(' -- ')[0]
                return target_value.strip()
        
        elif ' @hr ' in detail:
            parts = detail.split(' @hr ')
            if len(parts) >= 2:
                # Rimuovi la descrizione, se presente
                target_value = parts[1]
                if ' -- ' in target_value:
                    target_value = target_value.split(' -- ')[0]
                return target_value.strip()
        
        elif ' @pwr ' in detail:
            parts = detail.split(' @pwr ')
            if len(parts) >= 2:
                # Rimuovi la descrizione, se presente
                target_value = parts[1]
                if ' -- ' in target_value:
                    target_value = target_value.split(' -- ')[0]
                return target_value.strip()
        
        elif ' @cad ' in detail:
            parts = detail.split(' @cad ')
            if len(parts) >= 2:
                # Rimuovi la descrizione, se presente
                target_value = parts[1]
                if ' -- ' in target_value:
                    target_value = target_value.split(' -- ')[0]
                return target_value.strip()
        
        return ""
        
    def update_preview(self):
        """Aggiorna l'anteprima del passo."""
        try:
            step_type = self.step_type_var.get()
            end_condition = self.end_condition_var.get()
            
            # Costruisci la stringa di base con la condizione di fine
            if end_condition == "lap.button":
                preview = "lap-button"
            else:
                preview = self.end_value_var.get()
            
            # Aggiungi il target, se presente
            target_type = self.target_var.get()
            
            if target_type != "no.target":
                target_value = getattr(self, 'target_value_var', tk.StringVar()).get()
                
                if target_type == "pace.zone":
                    preview += f" @ {target_value}"
                elif target_type == "heart.rate.zone":
                    preview += f" @hr {target_value}"
                elif target_type == "power.zone":
                    preview += f" @pwr {target_value}"
                elif target_type == "speed.zone":
                    preview += f" @spd {target_value}"
                elif target_type == "cadence.zone":
                    preview += f" @cad {target_value}"
            
            # Aggiungi la descrizione, se presente
            description = self.description_var.get().strip()
            if description:
                preview += f" -- {description}"
            
            # Aggiorna la variabile di anteprima
            self.preview_var.set(f"{step_type}: {preview}")
            
        except Exception as e:
            self.preview_var.set(f"Errore nell'anteprima: {str(e)}")
    
    def _get_config_paces(self):
        """
        Ottiene i ritmi predefiniti dalla configurazione.
        
        Returns:
            list: Opzioni di ritmo
        """
        # Accedi alla configurazione attraverso la gerarchia parent
        try:
            if hasattr(self.parent, 'controller') and hasattr(self.parent.controller, 'config'):
                config = self.parent.controller.config
                if 'workout_config' in config and 'paces' in config['workout_config']:
                    paces = config['workout_config']['paces']
                    
                    # Crea una lista di opzioni nel formato "nome (valore)"
                    options = []
                    for name in paces.keys():
                        options.append(name)
                    
                    if not options:
                        options = ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "marathon"]
                        
                    return options
            
            # Se non riesce ad accedere alla configurazione, usa valori di default
            return ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "marathon"]
        except:
            return ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "marathon"]

    def _get_config_heart_rates(self):
        """
        Ottiene le zone di frequenza cardiaca predefinite dalla configurazione.
        
        Returns:
            list: Opzioni di zona di frequenza cardiaca
        """
        # Accedi alla configurazione attraverso la gerarchia parent
        try:
            if hasattr(self.parent, 'controller') and hasattr(self.parent.controller, 'config'):
                config = self.parent.controller.config
                if 'workout_config' in config and 'heart_rates' in config['workout_config']:
                    heart_rates = config['workout_config']['heart_rates']
                    
                    # Filtra per escludere max_hr
                    options = []
                    for name in heart_rates.keys():
                        if name != 'max_hr':
                            options.append(name)
                    
                    if not options:
                        options = ["Z1_HR", "Z2_HR", "Z3_HR", "Z4_HR", "Z5_HR"]
                        
                    return options
            
            # Se non riesce ad accedere alla configurazione, usa valori di default
            return ["Z1_HR", "Z2_HR", "Z3_HR", "Z4_HR", "Z5_HR"]
        except:
            return ["Z1_HR", "Z2_HR", "Z3_HR", "Z4_HR", "Z5_HR"]

    def _get_config_power_zones(self):
        """
        Ottiene le zone di potenza predefinite dalla configurazione.
        
        Returns:
            list: Opzioni di zona di potenza
        """
        # Accedi alla configurazione attraverso la gerarchia parent
        try:
            if hasattr(self.parent, 'controller') and hasattr(self.parent.controller, 'config'):
                config = self.parent.controller.config
                if 'workout_config' in config and 'power_values' in config['workout_config']:
                    power_values = config['workout_config']['power_values']
                    
                    # Filtra per escludere ftp
                    options = []
                    for name in power_values.keys():
                        if name != 'ftp':
                            options.append(name)
                    
                    if not options:
                        options = ["Z1", "Z2", "Z3", "Z4", "Z5", "threshold", "sweet_spot"]
                        
                    return options
            
            # Se non riesce ad accedere alla configurazione, usa valori di default
            return ["Z1", "Z2", "Z3", "Z4", "Z5", "threshold", "sweet_spot"]
        except:
            return ["Z1", "Z2", "Z3", "Z4", "Z5", "threshold", "sweet_spot"]