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

def listar_reservas_en_proceso(r):
    # Recorre todas las claves reserva_temp:* con SCAN
    cursor = 0
    reservas = []
    while True:
        cursor, keys = r.scan(cursor=cursor, match="reserva_temp:*", count=100)
        for k in keys:
            data = r.hgetall(k)  # {'usuario_id': '1', 'destino_id':'3', 'precio':'...', 'estado':'pendiente'}
        if cursor == 0:
            break
    return reservas

def imprimir_reservas_en_proceso(r):
    reservas = listar_reservas_en_proceso(r)
    if not reservas:
        print("No hay reservas en proceso.")
        return
    print("Reservas en proceso (pendientes):")
    print("-" * 60)
    for res in reservas:
        print(f"ID: {res['id_reserva']} | Usuario: {res['usuario']} (#{res['usuario_id']})")
        print(f"Destino: {res['destino']} (#{res['destino_id']})")
        print(f"Precio: ${res['precio']:.2f} | TTL: {res['ttl_seg']}s")
        print("-" * 60)

# Uso:
# imprimir_reservas_en_proceso(r, db)

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

def recomendar_destino_sin_visitar(driver, usuarioId):
    query = """
    MATCH (u:Usuario {usuario_id: $usuarioId})
    MATCH (d:Destino)
    WHERE NOT (u)-[:VISITO]->(d)
        AND NOT (u)-[:AMIGO_DE]-(:Usuario)-[:VISITO]->(d)
    RETURN DISTINCT d
    ORDER BY d.ciudad
    """
    
    with driver.session() as s:
        result = s.run(query, usuarioId=usuarioId).data()

    return result

def recomendar_destino_de_amigos(driver, usuarioId):
    query = """
    MATCH (u:Usuario {usuario_id: $usuarioId})
    MATCH (u)-[:AMIGO_DE]-(:Usuario)-[:VISITO]->(d)
    RETURN DISTINCT d
    ORDER BY d.ciudad
    """
    
    with driver.session() as s:
        result = s.run(query, usuarioId=usuarioId).data()

    return result