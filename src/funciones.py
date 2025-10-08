from pymongo import MongoClient

def cargar_usuario(usuarios):
    for elem in usuarios:
        usurrio_id = elem[0]