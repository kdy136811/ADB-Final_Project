import psycopg2

def recommend_user_by_equipment(input:str):
    # Update connection string information
    host = "127.0.0.1"
    dbname = "postgis_lab"
    user = "postgres"
    password = "0000"
    sslmode = "disable"
    # Construct connection string
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    conn = psycopg2.connect(conn_string)

    cursor = conn.cursor()
    cursor.execute("Select u2.uid From user_equipment u1, user_equipment u2 Where u1.uid = " + input + " and u1.uid != u2.uid and st_distance(u1.geog,u2.geog) < 50000;");
    output = cursor.fetchall()

    # Clean up
    conn.commit()
    cursor.close()
    conn.close()
    return output
	
def postgres_create_user_equipments(uhave_id: int, uid: int, eid: int ,Longitude:float,Latitude:float,Altitude:float):
    # Update connection string information
    host = "127.0.0.1"
    dbname = "postgis_lab"
    user = "postgres"
    password = "0000"
    sslmode = "disable"
    # Construct connection string
    conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
    conn = psycopg2.connect(conn_string)

    cursor = conn.cursor()
    cursor.execute("SELECT ST_GeomFromText('POINT(" + str(Longitude) + " " + str(Latitude) + ")', 4326);")
    temp = cursor.fetchall()
    geom = temp[0][0]
    cursor.execute("SELECT ST_GeogFromText('SRID=4326;POINT(" + str(Longitude) + " " + str(Latitude) + ")');")
    temp = cursor.fetchall()
    geog = temp[0][0]
    cursor.execute("INSERT INTO user_equipment (uhave_id, UID, EID, longitude, latitude, altitude, geom, geog) VALUES (" + str(uhave_id) + ", " + str(uid) + ", " + str(eid) + ", " + str(Longitude) + ", " + str(Latitude) + ", " + str(Altitude) + ", '" + geom + "', '" + geog + "');")
    # Clean up
    conn.commit()
    cursor.close()
    conn.close()
    return  
#postgres_create_user_equipments(3003,0,1,123.1,20.1,200.0)
	