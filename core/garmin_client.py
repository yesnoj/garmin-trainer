#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client per interagire con Garmin Connect.
Basato sul client originale di garmin-planner, ma esteso per supportare
più tipi di sport e più funzionalità.
"""

import json
import logging
import os
import datetime
from getpass import getpass
import garth

class GarminClient:
    """Client per interagire con l'API di Garmin Connect"""

    def __init__(self, oauth_folder='~/.garth'):
        """
        Inizializza il client Garmin Connect.
        
        Args:
            oauth_folder: Cartella dove sono memorizzati i token OAuth
        """
        # Disabilita la verifica SSL a livello globale
        import ssl
        import requests
        from urllib3.exceptions import InsecureRequestWarning
        
        # Disattiva gli avvisi di sicurezza per le richieste non verificate
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        
        # Configura un contesto SSL non verificato
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Espandi il percorso della home se necessario
        self.oauth_folder = os.path.normpath(os.path.expanduser(oauth_folder))
        
        # Crea la directory se non esiste
        os.makedirs(self.oauth_folder, exist_ok=True)
        
        # Configura garth per disabilitare la verifica SSL
        try:
            import garth
            garth.configure(verify_ssl=False)
        except:
            pass
        
        # Prova a riprendere la sessione esistente
        try:
            garth.resume(self.oauth_folder)
            self.logged_in = True
        except Exception as e:
            logging.warning(f"Impossibile riprendere la sessione: {str(e)}")
            self.logged_in = False

    def login(self, email, password, save_token=True):
        """
        Effettua il login su Garmin Connect.
        
        Args:
            email: Email dell'account Garmin
            password: Password dell'account Garmin
            save_token: Se True, salva il token per utilizzi futuri
            
        Returns:
            bool: True se il login è riuscito, False altrimenti
        """
        try:
            # Disabilita gli avvisi SSL
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Disabilita la verifica SSL in garth 
            import ssl
            original_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # Effettua il login
            garth.login(email, password)
            self.logged_in = True
            
            # Ripristina il contesto SSL originale
            ssl._create_default_https_context = original_context
            
            if save_token:
                garth.save(self.oauth_folder)
                
            return True
        except Exception as e:
            logging.error(f"Errore durante il login: {str(e)}")
            self.logged_in = False
            return False

    def list_workouts(self, limit=999):
        """
        Ottiene la lista degli allenamenti da Garmin Connect.
        
        Args:
            limit: Numero massimo di allenamenti da recuperare
            
        Returns:
            list: Lista degli allenamenti
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        response = garth.connectapi(
            '/workout-service/workouts',
            params={'start': 1, 'limit': limit, 'myWorkoutsOnly': True})
        
        return response

    def add_workout(self, workout):
        """
        Aggiunge un nuovo allenamento a Garmin Connect.
        
        Args:
            workout: Oggetto Workout da aggiungere
            
        Returns:
            dict: Risposta dell'API
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        response = garth.connectapi(
            '/workout-service/workout', method="POST",
            json=workout.garminconnect_json())
            
        return response 

    def delete_workout(self, workout_id):
        """
        Elimina un allenamento da Garmin Connect.
        
        Args:
            workout_id: ID dell'allenamento da eliminare
            
        Returns:
            dict: Risposta dell'API
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        logging.info(f'Eliminazione allenamento {workout_id}')
        response = garth.connectapi(
            '/workout-service/workout/' + str(workout_id), method="DELETE")
            
        return response 

    def get_workout(self, workout_id):
        """
        Ottiene i dettagli di un allenamento specifico.
        
        Args:
            workout_id: ID dell'allenamento
            
        Returns:
            dict: Dettagli dell'allenamento
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        logging.info(f'Recupero allenamento {workout_id}')
        response = garth.connectapi(
            '/workout-service/workout/' + str(workout_id), method="GET")
            
        return response 

    def update_workout(self, workout_id, workout):
        """
        Aggiorna un allenamento esistente.
        
        Args:
            workout_id: ID dell'allenamento da aggiornare
            workout: Oggetto Workout con i nuovi dati
            
        Returns:
            dict: Risposta dell'API
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        logging.info(f'Aggiornamento allenamento {workout_id}')
        wo_json = workout.garminconnect_json()
        wo_json['workoutId'] = workout_id
        
        response = garth.connectapi(
            '/workout-service/workout/' + str(workout_id), method="PUT", json=wo_json)
            
        return response 

    def get_calendar(self, year, month):
        """
        Ottiene il calendario per un mese specifico.
        
        Args:
            year: Anno
            month: Mese (1-12)
            
        Returns:
            dict: Dati del calendario
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        logging.info(f'Recupero calendario. Anno: {year}, mese: {month}')
        response = garth.connectapi(
            f'/calendar-service/year/{year}/month/{month-1}')
            
        return response 

    def schedule_workout(self, workout_id, date):
        """
        Pianifica un allenamento su una data specifica.
        
        Args:
            workout_id: ID dell'allenamento
            date: Data (stringa YYYY-MM-DD o oggetto datetime)
            
        Returns:
            dict: Risposta dell'API
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        date_formatted = date
        if not isinstance(date_formatted, str):
            date_formatted = date.strftime('%Y-%m-%d')
            
        response = garth.connectapi(
            f'/workout-service/schedule/{workout_id}', method="POST",
            json={'date': date_formatted})
            
        return response 

    def unschedule_workout(self, schedule_id):
        """
        Rimuove la pianificazione di un allenamento.
        
        Args:
            schedule_id: ID della pianificazione
            
        Returns:
            dict: Risposta dell'API
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        response = garth.connectapi(
            f'/workout-service/schedule/{schedule_id}', method="DELETE")
            
        return response 

    def get_user_profile(self):
        """
        Ottiene il profilo dell'utente.
        
        Returns:
            dict: Dati del profilo utente
        """
        if not self.logged_in:
            raise Exception("Non sei autenticato. Effettua prima il login.")
            
        response = garth.connectapi('/userprofile-service/userprofile')
        return response

    def is_logged_in(self):
        """
        Verifica se il client è attualmente loggato.
        
        Returns:
            bool: True se il client è loggato, False altrimenti
        """
        return self.logged_in

    def logout(self):
        """
        Effettua il logout dall'account Garmin.
        
        Returns:
            bool: True se il logout è riuscito, False altrimenti
        """
        try:
            garth.client.clear()
            self.logged_in = False
            
            # Rimuovi il file del token, se esiste
            token_file = os.path.join(self.oauth_folder, 'token.json')
            if os.path.exists(token_file):
                os.remove(token_file)
                
            return True
        except Exception as e:
            logging.error(f"Errore durante il logout: {str(e)}")
            return False