#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per il login a Garmin Connect.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import os

from ..core.garmin_client import GarminClient


class LoginFrame(ttk.Frame):
    """Frame per il login a Garmin Connect."""
    
    def __init__(self, parent, controller):
        """
        Inizializza il frame di login.
        
        Args:
            parent: Widget genitore
            controller: Controller dell'applicazione
        """
        super().__init__(parent)
        self.controller = controller
        
        # Ottieni le impostazioni di login dalla configurazione
        oauth_folder = self.controller.config.get('oauth_folder', '~/.garth')
        saved_email = self.controller.config.get('email', '')
        
        # Variabili per i campi di input
        self.email_var = tk.StringVar(value=saved_email)
        self.password_var = tk.StringVar()
        self.save_token_var = tk.BooleanVar(value=True)
        self.oauth_folder_var = tk.StringVar(value=oauth_folder)
        
        # Indicatore di stato di login
        self.logged_in = False
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Controlla se esiste già un token salvato
        self.check_saved_token()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        # Contenitore principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titolo
        title_label = ttk.Label(
            main_frame, 
            text="Login a Garmin Connect", 
            style="Heading.TLabel"
        )
        title_label.pack(pady=(0, 20))
        
        # Frame per i controlli di login
        login_frame = ttk.Frame(main_frame)
        login_frame.pack(fill=tk.X, pady=10)
        
        # Email
        email_label = ttk.Label(login_frame, text="Email:")
        email_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        email_entry = ttk.Entry(login_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Password
        password_label = ttk.Label(login_frame, text="Password:")
        password_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        password_entry = ttk.Entry(login_frame, textvariable=self.password_var, 
                                show="*", width=30)
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Opzione per salvare il token
        save_token_check = ttk.Checkbutton(
            login_frame, 
            text="Salva token per futuri accessi", 
            variable=self.save_token_var
        )
        save_token_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Cartella OAuth
        oauth_frame = ttk.Frame(login_frame)
        oauth_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        oauth_label = ttk.Label(oauth_frame, text="Cartella token:")
        oauth_label.pack(side=tk.LEFT)
        
        oauth_entry = ttk.Entry(oauth_frame, textvariable=self.oauth_folder_var, width=30)
        oauth_entry.pack(side=tk.LEFT, padx=5)
        
        # Pulsanti
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.login_button = ttk.Button(
            button_frame, 
            text="Login", 
            command=self.login,
            style="Success.TButton",
            width=15
        )
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        self.logout_button = ttk.Button(
            button_frame, 
            text="Logout", 
            command=self.logout,
            style="Danger.TButton",
            width=15,
            state=tk.DISABLED
        )
        self.logout_button.pack(side=tk.LEFT, padx=5)
        
        # Indicatore di stato
        self.status_label = ttk.Label(
            login_frame, 
            text="Non connesso", 
            style="Status.TLabel"
        )
        self.status_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Istruzioni
        instructions_frame = ttk.LabelFrame(main_frame, text="Istruzioni")
        instructions_frame.pack(fill=tk.X, pady=10)
        
        instructions_text = (
            "Per utilizzare Garmin Trainer, è necessario effettuare il login al tuo account Garmin Connect.\n\n"
            "1. Inserisci la tua email e password di Garmin Connect\n"
            "2. Seleziona 'Salva token' per non dover inserire le credenziali ogni volta\n"
            "3. Fai clic su 'Login'\n\n"
            "Note: Le credenziali non vengono conservate, solo il token di accesso."
        )
        
        instructions_label = ttk.Label(
            instructions_frame, 
            text=instructions_text,
            wraplength=500, 
            justify=tk.LEFT
        )
        instructions_label.pack(padx=10, pady=10)
    
    def check_saved_token(self):
        """Verifica se esiste un token salvato per il login automatico."""
        oauth_folder = os.path.expanduser(self.oauth_folder_var.get())
        token_path = os.path.join(oauth_folder, 'token.json')
        
        if os.path.exists(token_path):
            try:
                # Crea un client e verifica se il token è valido
                client = GarminClient(oauth_folder)
                if client.is_logged_in():
                    self.on_login_success(client)
                    logging.info("Login automatico effettuato con token esistente.")
                    return
            except Exception as e:
                logging.warning(f"Token esistente non valido: {str(e)}")
        
        # Se arriviamo qui, non c'è un token valido
        logging.info("Nessun token valido trovato, login manuale richiesto.")
    
    def login(self):
        """Esegue il login a Garmin Connect."""
        # Disabilita i controlli durante il login
        self.login_button['state'] = tk.DISABLED
        self.status_label['text'] = "Login in corso..."
        
        # Aggiorna l'interfaccia
        self.update()
        
        # Crea un thread separato per il login
        threading.Thread(target=self._login_thread, daemon=True).start()
    
    def _login_thread(self):
        """Thread separato per eseguire il login senza bloccare l'interfaccia."""
        try:
            # Ottieni i dati dal form
            email = self.email_var.get()
            password = self.password_var.get()
            save_token = self.save_token_var.get()
            oauth_folder = self.oauth_folder_var.get()
            
            # Validazione
            if not email or not password:
                self.after(0, lambda: messagebox.showerror(
                    "Errore", 
                    "Email e password sono obbligatorie.", 
                    parent=self
                ))
                self.after(0, self._update_ui_after_login_failure)
                return
            
            # Crea il client
            client = GarminClient(oauth_folder)
            
            # Esegui il login
            success = client.login(email, password, save_token)
            
            if success:
                # Aggiorna la configurazione
                self.controller.config['oauth_folder'] = oauth_folder
                if save_token:
                    self.controller.config['email'] = email
                self.controller.save_config()
                
                # Aggiorna l'interfaccia
                self.after(0, lambda: self.on_login_success(client))
            else:
                # Mostra errore
                self.after(0, lambda: messagebox.showerror(
                    "Errore di login", 
                    "Impossibile accedere con le credenziali fornite.", 
                    parent=self
                ))
                self.after(0, self._update_ui_after_login_failure)
        
        except Exception as e:
            # Gestisci qualsiasi errore
            logging.error(f"Errore durante il login: {str(e)}")
            self.after(0, lambda: messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il login: {str(e)}", 
                parent=self
            ))
            self.after(0, self._update_ui_after_login_failure)
    
    def _update_ui_after_login_failure(self):
        """Aggiorna l'interfaccia dopo un login fallito."""
        self.login_button['state'] = tk.NORMAL
        self.status_label['text'] = "Non connesso"
    
    def on_login_success(self, client):
        """
        Aggiorna l'interfaccia dopo un login riuscito.
        
        Args:
            client: Istanza di GarminClient con login effettuato
        """
        # Aggiorna lo stato
        self.logged_in = True
        
        # Aggiorna i pulsanti
        self.login_button['state'] = tk.DISABLED
        self.logout_button['state'] = tk.NORMAL
        
        # Aggiorna l'etichetta di stato
        self.status_label['text'] = "Connesso a Garmin Connect"
        
        # Passa il client al controller
        self.controller.set_garmin_client(client)
        
        # Aggiorna il messaggio di stato generale
        self.controller.set_status("Connesso a Garmin Connect")
        
        # Mostra notifica
        messagebox.showinfo(
            "Login effettuato", 
            "Hai effettuato il login a Garmin Connect con successo!", 
            parent=self
        )
    
    def logout(self):
        """Esegue il logout da Garmin Connect."""
        if not self.controller.garmin_client:
            return
        
        # Chiedi conferma
        if not messagebox.askyesno(
            "Conferma logout", 
            "Sei sicuro di voler effettuare il logout da Garmin Connect?", 
            parent=self
        ):
            return
        
        # Esegui il logout
        try:
            success = self.controller.garmin_client.logout()
            
            if success:
                # Aggiorna lo stato
                self.logged_in = False
                
                # Aggiorna i pulsanti
                self.login_button['state'] = tk.NORMAL
                self.logout_button['state'] = tk.DISABLED
                
                # Aggiorna l'etichetta di stato
                self.status_label['text'] = "Non connesso"
                
                # Reset del client nel controller
                self.controller.set_garmin_client(None)
                
                # Aggiorna il messaggio di stato generale
                self.controller.set_status("Logout effettuato")
                
                # Mostra notifica
                messagebox.showinfo(
                    "Logout effettuato", 
                    "Hai effettuato il logout da Garmin Connect con successo.", 
                    parent=self
                )
            else:
                # Mostra errore
                messagebox.showerror(
                    "Errore di logout", 
                    "Impossibile effettuare il logout.", 
                    parent=self
                )
        
        except Exception as e:
            # Gestisci qualsiasi errore
            logging.error(f"Errore durante il logout: {str(e)}")
            messagebox.showerror(
                "Errore", 
                f"Si è verificato un errore durante il logout: {str(e)}", 
                parent=self
            )