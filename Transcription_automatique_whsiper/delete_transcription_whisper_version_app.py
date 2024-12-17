import sys
sys.path.insert(0, '/mnt/c/Users/utilisateur/Documents/newvenv/okapi')
from okapi_api import okapi_login, sparql_search, sparql_admin, remove_transcription
import tkinter as tk
from tkinter import messagebox
from rdflib import  Dataset
from ina_utilities import convert_seconds_to_MPEG7, convert_Okapi_time_to_timeRef, convert_timeRef_to_MPEG7, remove_layer_from_kb


"""
Fonction : Ce programme propose une interface utilisateur permettant de enlever une transcription de vidéo sur LaCAS.
Entrée : 
- Compte administratif LaCAS : Identifiants nécessaires pour se connecter à la plateforme.
- Titre de transcription à enlever
Soritie : rien
Méthodes d'utilisation :
1. Se connecter : Saisissez les informations de votre compte administratif LaCAS, puis cliquez sur "Login".
2. Saisir le titre de transciption à supprimer
3. Lancer le programme : Cliquer sur 'Remove the transcription'
"""

opener = None
okapi_url = 'https://lacas.inalco.fr/portals'
kb = Dataset()

def get_video_uri(okapi_url, opener, title):
    query =f'''
    PREFIX core: <http://www.ina.fr/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT DISTINCT ?media ?url ?creationdate
        WHERE {{
        ?media a core:TemporalDocument .
        ?layer core:document ?media .
        ?layer core:segment ?media_segment .
        ?media_segment dc:title "{title}"@fr .
        ?media_segment core:creationDate ?creationdate .
        ?media core:instance ?instance .
        ?instance core:http_url ?url .
        }}ORDER BY ?creationdate
    '''
    answer = sparql_search(okapi_url, query, opener)
    if answer:
        for result in answer:
            media_value = result["media"]["value"]
    else : 
        messagebox.showwarning('Warning', 'Please check the title of the transcription')
    return media_value

def remove_transcription(base_url, media_ref, opener):
    try : 
        update_query = """
                PREFIX core: <http://www.ina.fr/core#>
                delete {graph ?g {?s ?p ?o}}
                where {
                ?layer a core:ASRLayer .
                ?layer core:document <""" + media_ref + """> .
                { graph ?layer {?s ?p ?o}.
                    BIND (?layer as ?g)}
                UNION {
                    ?layer core:segment ?g .
                    graph ?g {?s ?p ?o}}
                }"""
        answer = sparql_admin(base_url, update_query, opener)
        print(answer)
        if answer : 
            messagebox.showinfo("Success", "Transcription files are now removed from LaCAS")
    except Exception as e:
        messagebox.showerror('Query failed', f'An error occurred during the query : {e}')

def login():
    global opener
    login = entry_login.get()
    passwd = entry_passwd.get()
    opener = okapi_login(okapi_url, login, passwd)
    messagebox.showinfo("Login", "Login successful.")
    output_text.insert(tk.END, f"Please enter the title of the video that needs transcription removal.\n")

def password():
    messagebox.showinfo("Password", "Password functionality not yet implemented.")

root = tk.Tk()
root.title("Delete the transcription tool")
root.geometry("600x400")

tk.Label(root, text="Login:").grid(row=0, column=0)
entry_login = tk.Entry(root)
entry_login.grid(row=0, column=1)
tk.Label(root, text="Password:").grid(row=1, column=0)
entry_passwd = tk.Entry(root, show="*")
entry_passwd.grid(row=1, column=1)

login_button = tk.Button(root, text="Login", command=login)
login_button.grid(row=2, column=0, columnspan=2, pady=5)

tk.Label(root, text='Title of the video').grid(row=3, column=0)
entry_title = tk.Entry(root)
entry_title.grid(row=3, column=1)

title_button = tk.Button(root, text="Remove the transcription", command= lambda : remove_transcription(okapi_url, get_video_uri(okapi_url, opener, entry_title.get()), opener))
title_button.grid(row=4, column=0, columnspan=2, pady=5)

output_text = tk.Text(root, wrap='word', height=10)
output_text.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
