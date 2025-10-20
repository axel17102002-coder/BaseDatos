from pymongo import MongoClient
import random, string


def cargar_datos(ruta, nombre_coleccion):
    with open(ruta, 'r', encoding='utf-8') as archivo_json:
        datos = json.load(archivo_json)

    coleccion = getattr(db, nombre_coleccion)

    if isinstance(datos, list):
        res = coleccion.insert_many(datos)
        return len(res.inserted_ids)
    else:
        res = coleccion.insert_one(datos)
        return 1
    
#def hacer_busqueda():

#Buscar usuario por nombre
def obtener_usuario_id(nombre):
    usuario = db.usuarios.find_one({"nombre": nombre})
    if usuario:
        return usuario["usuario_id"]
    else:
        return None

#Buscar destino por nombre
def obtener_destino_id(destino):
    destino = db.destinos.find_one({"ciudad": destino})
    if destino:
        return destino["destino_id"],destino['precio_promedio']
    else:
        return None

def crear_reserva(r,nombre,destino):
    usuario_id = obtener_usuario_id(nombre)
    def generar_id_reserva():
        prefijo = "RSV"
        numero = random.randint(1000, 9999)
        sufijo = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"{prefijo}-{numero}{sufijo}"
    destino_info = obtener_destino_id(destino)
    if not usuario_id or not destino_info:
        print("Error: usuario o destino no encontrado")
        return
    id_reserva = generar_id_reserva()
    key = f"reserva_temp:{id_reserva}"
    r.hset(key, mapping={
        "usuario_id": usuario_id,
        "destino_id": destino_info[0],
        "precio": random.random() * destino_info[1],
        "estado": "pendiente"
    })
    r.expire(key, 900)  # expira en 15 minutos
    print(f"✅ Reserva temporal creada: {id_reserva}")
    return id_reserva

def buscar_por_ciudad(driver, ciudad="Bariloche"):
    query = """
    MATCH (u:Usuario)-[:VISITO]->(d:Destino)
    WHERE d.ciudad = $ciudad
    RETURN u.usuario_id AS id, u.nombre AS nombre
    ORDER BY u.usuario_id
    """
    with driver.session() as s:
        result = s.run(query, ciudad=ciudad).data()
    return result

def buscar(driver,name):
    query = """
    MATCH (juan:Usuario {nombre: $name})-[:VISITO]->(d:Destino)
    MATCH (juan)-[:AMIGO_DE]-(amigo:Usuario)-[:VISITO]->(d)
    RETURN DISTINCT amigo.nombre AS amigo, d.ciudad AS destino
    ORDER BY amigo, destino
    """
    with driver.session() as s:
        result = s.run(query, nombre=name).data()
    return result