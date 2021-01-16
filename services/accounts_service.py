from data.db_session import db_auth
from typing import Optional
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from services.classes import User, Equipments


graph = db_auth()


def find_user(email: str):
    user = User.match(graph, f"{email}")
    return user


def create_user(name: str, email: str, company: str, password: str) -> Optional[User]:
    if find_user(email):
        return None
    user = User()
    user.name = name
    user.email = email
    user.company = company
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
    user_profile = graph.run(f"MATCH (x:user) WHERE x.email='{usr}' RETURN x.name as name, x.company as company, x.email as email").data()
    return user_profile

def update_profile(usr: str, name: str, company: str) -> Optional[User]:
    # user = User.match(graph, f"{usr}").first()
    user_profile = graph.run(f"MATCH (x:user) WHERE x.email='{usr}' SET x.name='{name}', x.company='{company}' RETURN x.name as name, x.company as company, x.email as email").data()
    return user_profile


def count_user_equipment(usr: str)->int:
    
    count = graph.run("MATCH (x:user {email:$usr})-[:have_e]->(:equipments) return count(*)",usr=usr).evaluate()
    return count

def create_user_equipments(usr: str,eid: str ,Site: str,Longitude:float,Latitude:float,Altitude:float,tz:str,daylight:bool,wv: float,light_pollusion: float):
    

    query = f"MATCH (x:user) where x.email='{usr}'  MATCH (e:equipments) where e.EID={eid}" \
    "CREATE (x)-[h:have_e{ uhaveid: $uhaveid, site:$Site, longitude:$Longitude, latitude:$Latitude" \
    ", altitude:$Altitude, time_zone:$tz, daylight_saving:$daylight, water_vapor:$wv,light_pollusion:$light_pollusion}]->(e) return h.uhaveid as id, h.site as site, h.longitude as longitude," \
    "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollusion as light_pollusion"

    count = graph.run("MATCH (x:user)-[p:have_e]->(:equipments) return count(*)").evaluate()    
    user_equipments = graph.run(query,Site=Site,Longitude=Longitude,Latitude=Latitude,Altitude=Altitude,tz=tz,daylight=daylight,wv=wv,light_pollusion=light_pollusion, uhaveid = count)
    return user_equipments

def update_user_equipments(aperture: float,Fov: float,pixel_scale: float,tracking_accurcy: float,lim_magnitude: float,elevation_lim: float,mount_type: str,camera_type1:str,
                          camera_type2: str,JohnsonB: str,JohnsonR: str,JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz:str,
                          usr: str ,Site: str,Longitude:float,Latitude:float,Altitude:float,tz:str,daylight:bool,wv: float,light_pollusion: float, uhaveid : int):

    print(uhaveid) 
    query ="MATCH (x:user {email:$usr})-[h:have_e {uhaveid: $uhaveid}]->(e:equipments)" \
             f"SET h.site='{Site}', h.longitude='{Longitude}', h.latitude='{Latitude}', h.altitude='{Altitude}', h.time_zone='{tz}', h.daylight_saving='{daylight}', h.water_vapor='{wv}'," \
             f"h.light_pollusion='{light_pollusion}', e.aperture='{aperture}', e.Fov='{Fov}', e.pixel_scale='{pixel_scale}',e.tracking_accurcy='{tracking_accurcy}', e.lim_magnitude='{lim_magnitude}',"\
             f"e.elevation_lim='{elevation_lim}', e.mount_type='{mount_type}', e.camera_type1='{camera_type1}', e.camera_type2='{camera_type2}', e.JohnsonB='{JohnsonB}', e.JohnsonR='{JohnsonR}', e.JohnsonV='{JohnsonV}', " \
             f"e.SDSSu='{SDSSu}', e.SDSSg='{SDSSg}', e.SDSSr='{SDSSr}', e.SDSSi='{SDSSi}', e.SDSSz='{SDSSz}'"  
    user_equipments = graph.run(query,usr = usr, uhaveid = uhaveid)
    return user_equipments

def get_user_equipments(usr: str):
    # return the user's equipment and that equipment's detail
    if  count_user_equipment(usr) == 0:
        return None
    user_equipments = graph.run("MATCH (x:user {email:$usr})-[h:have_e]->(e:equipments) return e.EID as eid,h.site as site, h.longitude as longitude," \
        "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollusion as light_pollusion," \
        "e.aperture as aperture, e.Fov as Fov, e.pixel_scale as pixel_scale,e.tracking_accurcy as  tracking_accurcy, e.lim_magnitude as lim_magnitude, e.elevation_lim as elevation_lim," \
        "e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2, e.JohnsonB as JohnsonB, e.JohnsonR as JohnsonR, e.JohnsonV as JohnsonV, e.SDSSu as SDSSu," \
        "e.SDSSg as SDSSg, e.SDSSr as SDSSr, e.SDSSi as SDSSi,e.SDSSz as SDSSz, h.uhaveid as id" ,usr=usr).data()
    return user_equipments

def create_equipments(aperture:float,Fov:float,pixel_scale:float,tracking_accurcy:float,lim_magnitude:float,elevation_lim:float,mount_type:str,camera_type1:str,camera_type2:str,JohsonB:str,JohsonR:str,JohsonV:str,SDSSu:str,SDSSg:str,SDSSr:str,SDSSi:str,SDSSz:str)->Optional[Equipments]:
    # create an equipment
    count = graph.run("MATCH (e:equipments) return count(*) as count").evaluate()
    equipment = Equipments()
    equipment.EID = count
    equipment.aperture = aperture
    equipment.Fov = Fov
    equipment.pixel_scale =pixel_scale
    equipment.tracking_accurcy = tracking_accurcy
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