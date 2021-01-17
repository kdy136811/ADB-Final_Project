from data.db_session import db_auth
from typing import Optional
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from services.classes import *


graph = db_auth()


def find_user(email: str):
    user = User.match(graph, f"{email}")
    return user


def create_user(username: str, name: str, email: str, affiliation: str, title: str, country: str, password: str) -> Optional[User]:
    if find_user(email):
        return None
    user = User()
    max_id = graph.run(f"MATCH (u:user) RETURN u.UID order by u.UID DESC LIMIT 1").data()
    if len(max_id) == 0:
        user.UID = 0
    else:
        user.UID = max_id[0]['u.UID']+1
    user.username = username
    user.name = name
    user.email = email
    user.affiliation = affiliation
    user.title = title
    user.country = country
    user.hashed_password = hash_text(password)
    graph.create(user)
    return user


def hash_text(text: str) -> str:
    hashed_text = crypto.encrypt(text, rounds=171204)
    return hashed_text


def verify_hash(hashed_text: str, plain_text: str) -> bool:
    return crypto.verify(plain_text, hashed_text)


def login_user(email: str, password: str) -> Optional[User]:
    user = User.match(graph, f"{email}").first()
    if not user:
        print(f"Invalid User - {email}")
        return None
    if not verify_hash(user.hashed_password, password):
        print(f"Invalid Password for {email}")
        return None
    print(f"User {email} passed authentication")
    return user


def get_profile(usr: str) -> Optional[User]:
    # user = User.match(graph, f"{usr}").first()
    user_profile = graph.run(f"MATCH (x:user) WHERE x.email='{usr}' RETURN x.username as username, x.name as name, x.email as email, x.affiliation as affiliation, x.title as title, x.country as country").data()
    return user_profile

def update_profile(usr: str, username: str, name: str, affiliation: str, title: str, country: str) -> Optional[User]:
    # user = User.match(graph, f"{usr}").first()
    query = f"MATCH (x:user) WHERE x.email='{usr}' SET x.username='{username}', x.name='{name}', x.affiliation='{affiliation}', x.title='{title}', x.country='{country}'" \
    "RETURN x.username as username, x.name as name, x.email as email, x.affiliation as affiliation, x.title as title, x.country as country"
    user_profile = graph.run(query).data()
    return user_profile


def count_user_equipment(usr: str)->int:
    
    count = graph.run("MATCH (x:user {email:$usr})-[:UhaveE]->(:equipments) return count(*)",usr=usr).evaluate()
    return count

def create_user_equipments(usr: str,eid: int ,Site: str,Longitude:float,Latitude:float,Altitude:float,tz:str,daylight:bool,wv: float,light_pollution: float):
    

    query ="MATCH (x:user {email:$usr})  MATCH (e:equipments {EID:$EID})" \
    "CREATE (x)-[h:UhaveE{ uhaveid: $uhaveid, site:$Site, longitude:$Longitude, latitude:$Latitude" \
    ", altitude:$Altitude, time_zone:$tz, daylight_saving:$daylight, water_vapor:$wv,light_pollution:$light_pollution}]->(e) return h.uhaveid as id, h.site as site, h.longitude as longitude," \
    "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollution as light_pollution"

    count = graph.run("MATCH (x:user)-[p:UhaveE]->(:equipments) return p.uhaveid order by p.uhaveid DESC limit 1").data()
    if len(count) == 0:
        uhaveid = 0
    else:
        uhaveid = count[0]['p.uhaveid']+1
    print(uhaveid)
    user_equipments = graph.run(query,usr=usr, EID = eid, Site=Site,Longitude=Longitude,Latitude=Latitude,Altitude=Altitude,tz=tz,daylight=daylight,wv=wv,light_pollution=light_pollution, uhaveid = uhaveid)
    return user_equipments

<<<<<<< HEAD
def update_user_equipments(aperture: float,Fov: float,pixel_scale: float,tracking_accuracy: float,lim_magnitude: float,elevation_lim: float,mount_type: str,camera_type1:str,
                          camera_type2: str,JohnsonB: str,JohnsonR: str,JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz:str,
                          usr: str ,Site: str,Longitude:float,Latitude:float,Altitude:float,tz:str,daylight:bool,wv: float,light_pollution: float, uhaveid : int):

    print(uhaveid) 
    query ="MATCH (x:user {email:$usr})-[h:UhaveE {uhaveid: $uhaveid}]->(e:equipments)" \
             f"SET h.site='{Site}', h.longitude='{Longitude}', h.latitude='{Latitude}', h.altitude='{Altitude}', h.time_zone='{tz}', h.daylight_saving='{daylight}', h.water_vapor='{wv}'," \
             f"h.light_pollution='{light_pollution}', e.aperture='{aperture}', e.Fov='{Fov}', e.pixel_scale='{pixel_scale}',e.tracking_accuracy='{tracking_accurcy}', e.lim_magnitude='{lim_magnitude}',"\
             f"e.elevation_lim='{elevation_lim}', e.mount_type='{mount_type}', e.camera_type1='{camera_type1}', e.camera_type2='{camera_type2}', e.JohnsonB='{JohnsonB}', e.JohnsonR='{JohnsonR}', e.JohnsonV='{JohnsonV}', " \
             f"e.SDSSu='{SDSSu}', e.SDSSg='{SDSSg}', e.SDSSr='{SDSSr}', e.SDSSi='{SDSSi}', e.SDSSz='{SDSSz}'"  
    user_equipments = graph.run(query,usr = usr, uhaveid = uhaveid)
=======
def update_user_equipments(aperture: float, Fov: float, pixel_scale: float, tracking_accurcy: float, lim_magnitude: float, elevation_lim: float, mount_type: str, camera_type1:str,
                          camera_type2: str, JohnsonB: str, JohnsonR: str, JohnsonV: str, SDSSu: str, SDSSg: str, SDSSr: str, SDSSi: str, SDSSz:str,
                          usr: str , Site: str, Longitude:float, Latitude:float, Altitude:float, tz:str, daylight:bool, wv: float, light_pollusion: float, uhaveid: int):

    print(uhaveid) 
    query ="MATCH (x:user {email:$usr})-[h:UhaveE {uhaveid: $uhaveid}]->(e:equipments)" \
            f"SET h.site='{Site}', h.longitude='{Longitude}', h.latitude='{Latitude}', h.altitude='{Altitude}', h.time_zone='{tz}', h.daylight_saving='{daylight}', h.water_vapor='{wv}'," \
            f"h.light_pollusion='{light_pollusion}', e.aperture='{aperture}', e.Fov='{Fov}', e.pixel_scale='{pixel_scale}',e.tracking_accurcy='{tracking_accurcy}', e.lim_magnitude='{lim_magnitude}',"\
            f"e.elevation_lim='{elevation_lim}', e.mount_type='{mount_type}', e.camera_type1='{camera_type1}', e.camera_type2='{camera_type2}', e.JohnsonB='{JohnsonB}', e.JohnsonR='{JohnsonR}', e.JohnsonV='{JohnsonV}', " \
            f"e.SDSSu='{SDSSu}', e.SDSSg='{SDSSg}', e.SDSSr='{SDSSr}', e.SDSSi='{SDSSi}', e.SDSSz='{SDSSz}'"  
    user_equipments = graph.run(query, usr=usr, uhaveid=uhaveid)
>>>>>>> d9f734957340f64ced4c7eba1684dcbd5dc786f5
    return user_equipments

def get_user_equipments(usr: str):
    # return the user's equipment and that equipment's detail
    if  count_user_equipment(usr) == 0:
        return None
    user_equipments = graph.run("MATCH (x:user {email:$usr})-[h:UhaveE]->(e:equipments) return e.EID as eid,h.site as site, h.longitude as longitude," \
        "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollution as light_pollution," \
        "e.aperture as aperture, e.Fov as Fov, e.pixel_scale as pixel_scale,e.tracking_accuracy as  tracking_accuracy, e.lim_magnitude as lim_magnitude, e.elevation_lim as elevation_lim," \
        "e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2, e.JohnsonB as JohnsonB, e.JohnsonR as JohnsonR, e.JohnsonV as JohnsonV, e.SDSSu as SDSSu," \
        "e.SDSSg as SDSSg, e.SDSSr as SDSSr, e.SDSSi as SDSSi,e.SDSSz as SDSSz, h.uhaveid as id" ,usr=usr).data()
    return user_equipments

def delete_user_equipment(usr: str,uhaveid: int):
    #delete user's equipment
    graph.run("MATCH (x:user {email:$usr})-[h:UhaveE {uhaveid: $uhaveid}]->(e:equipments) DELETE h,e", usr=usr, uhaveid=uhaveid)


def create_equipments(aperture:float,Fov:float,pixel_scale:float,tracking_accuracy:float,lim_magnitude:float,elevation_lim:float,mount_type:str,camera_type1:str,camera_type2:str,JohsonB:str,JohsonR:str,JohsonV:str,SDSSu:str,SDSSg:str,SDSSr:str,SDSSi:str,SDSSz:str)->Optional[Equipments]:
    # create an equipment
    count = graph.run("MATCH (e:equipments) return e.EID  order by e.EID DESC limit 1 ").data()

    equipment = Equipments()
    if len(count) == 0:
        equipment.EID = 0
    else:
        equipment.EID = count[0]['e.EID']+1
    equipment.aperture = aperture
    equipment.Fov = Fov
    equipment.pixel_scale =pixel_scale
    equipment.tracking_accuracy = tracking_accuracy
    equipment.lim_magnitude =lim_magnitude
    equipment.elevation_lim = elevation_lim
    equipment.mount_type = mount_type
    equipment.camera_type1 = camera_type2
    equipment.camera_type2 = camera_type1
    equipment.JohnsonB = JohsonB
    equipment.JohnsonR = JohsonR
    equipment.JohnsonV = JohsonV
    equipment.SDSSu = SDSSu
    equipment.SDSSg = SDSSg
    equipment.SDSSr = SDSSr
    equipment.SDSSi = SDSSi
    equipment.SDSSz = SDSSz
    graph.create(equipment)
    return equipment



'''def get_equipments(usr:str)->Optional[Equipments]:
    
    equipment = graph.run("MATCH (x:usrr {email:$usr})-[h:have_e]->(e:equipment) return e.EID as eid, e.aperture as aperture, e.Fov as Fov, e.pixel_scale as pixel_scale," \
                           "e.tracking_accurcy as  tracking_accurcy, e.lim_magnitude as lim_magnotude, e.elevation_lim as elevation_lim, e.mount_type as mount_type, e.camera_type1 as camer_type1," \
                           "e.camera_type2 as camera_type2, e.JohnsonB as JohnsonB, e.JohnsonR as JohnsonR, e.JohnsonV as JohnsonV, e.SDSSu as SDSSu, e.SDSSg as SDSSg, e.SDSSr as SDSSr, e.SDSSi as SDSSi," \
                           "e.SDSSz as SDSSz", usr = usr).data()
    print(equipment)
    return equipment  
'''   

def get_target():
    # this function will return all target
    query = "MATCH(t:target) return t.name as name order by t.TID limit 100"
    # "MATCH(t:target) where t.tid>100 return t.name as name order by t.TID limit 100"
    target = graph.run(query)
    return target

def get_project(usr: str)->Optional[Project]:
    # this function will return project which user can join

    query = "MATCH (x:user {email:$usr})-[rel:UhaveE]->(e:equipments), (n:project) where n.mount_type=e.mount_type and n.camera_type1=e.camera_type1 and n.camera_type2=e.camera_type2 " \
        "and n.JohnsonB=e.JohnsonB and n.JohnsonV=e.JohnsonV and n.JohnsonR=e.JohnsonR  and n.SDSSu=e.SDSSu  and n.SDSSg=e.SDSSg and n.SDSSr=e.SDSSr and n.SDSSi=e.SDSSi and n.SDSSz=e.SDSSz" \
        " return n.title as title, n.project_type as project_type, n.PI as PI, n.description as description, n.aperture_upper_limit as aperture_upper_limit, n.aperture_lower_limit as aperture_lower_limit," \
        "n.FoV_upper_limit as FoV_upper_limit, n.FoV_lower_limit as FoV_lower_limit, n.pixel_scale_upper_limit as pixel_scale_upper_limit, n.pixel_scale_lower_limit as pixel_scale_lower_limit," \
        "n.mount_type as mount_type, n.camera_type1 as camera_type1, n.camera_type2 as camera_type2, n.JohnsonB as JohnsonB, n.JohnsonR as JohnsonR, n.JohnsonV as JohnsonV, n.SDSSu as SDSSu," \
        "n.SDSSg as SDSSg, n.SDSSr as SDSSr, n.SDSSi as SDSSi, n.SDSSz as SDSSz, n.PID as PID ORDER BY n.PID"
    project = graph.run(query, usr = usr)
    return project