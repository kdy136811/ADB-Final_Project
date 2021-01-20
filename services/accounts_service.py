from data.db_session import db_auth
from typing import Optional
from passlib.handlers.sha2_crypt import sha512_crypt as crypto
from services.classes import User, Target, Equipments, Project, Schedule
from datetime import datetime, timedelta


import services.declination_limit_of_location as declination
import services.astroplan_calculations as schedule
import services.nighttime_calculations as night
import ephem

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
    ", altitude:$Altitude, time_zone:$tz, daylight_saving:$daylight, water_vapor:$wv,light_pollution:$light_pollution, declination_limit:$declination_limit}]->(e) return h.uhaveid as id, h.site as site, h.longitude as longitude," \
    "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollution as light_pollution"

    count = graph.run("MATCH (x:user)-[p:UhaveE]->(:equipments) return p.uhaveid order by p.uhaveid DESC limit 1").data()
    if len(count) == 0:
        uhaveid = 0
    else:
        uhaveid = count[0]['p.uhaveid']+1
    print(uhaveid)
    user_equipments = graph.run(query,usr=usr, EID = eid, Site=Site,Longitude=Longitude,Latitude=Latitude,Altitude=Altitude,tz=tz,daylight=daylight,wv=wv,light_pollution=light_pollution, uhaveid = uhaveid, declination_limit=0)
    
    # calculate the declination limit of the equipment and update the table
    update_declination(uhaveid)

    # create a empty schedule for the equipment
    create_schedule(eid, uhaveid)

    return user_equipments

def update_user_equipments(aperture: float,Fov: float,pixel_scale: float,tracking_accuracy: float,lim_magnitude: float,elevation_lim: float,mount_type: str,camera_type1:str,
                          camera_type2: str,JohnsonB: str,JohnsonR: str,JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz:str,
                          usr: str ,Site: str,Longitude:float,Latitude:float,Altitude:float,tz:str,daylight:bool,wv: float,light_pollution: float, uhaveid : int):

    print(uhaveid) 
    query ="MATCH (x:user {email:$usr})-[h:UhaveE {uhaveid: $uhaveid}]->(e:equipments)" \
             f"SET h.site='{Site}', h.longitude='{Longitude}', h.latitude='{Latitude}', h.altitude='{Altitude}', h.time_zone='{tz}', h.daylight_saving='{daylight}', h.water_vapor='{wv}'," \
             f"h.light_pollution='{light_pollution}', e.aperture='{aperture}', e.Fov='{Fov}', e.pixel_scale='{pixel_scale}',e.tracking_accuracy='{tracking_accuracy}', e.lim_magnitude='{lim_magnitude}',"\
             f"e.elevation_lim='{elevation_lim}', e.mount_type='{mount_type}', e.camera_type1='{camera_type1}', e.camera_type2='{camera_type2}', e.JohnsonB='{JohnsonB}', e.JohnsonR='{JohnsonR}', e.JohnsonV='{JohnsonV}', " \
             f"e.SDSSu='{SDSSu}', e.SDSSg='{SDSSg}', e.SDSSr='{SDSSr}', e.SDSSi='{SDSSi}', e.SDSSz='{SDSSz}'"  
    user_equipments = graph.run(query,usr = usr, uhaveid = uhaveid)
    update_declination(uhaveid)
    return user_equipments

def get_user_equipments(usr: str):
    # return the user's equipment and that equipment's detail
    if  count_user_equipment(usr) == 0:
        return None
    user_equipments = graph.run("MATCH (x:user {email:$usr})-[h:UhaveE]->(e:equipments) return e.EID as eid,h.site as site, h.longitude as longitude," \
        "h.latitude as latitude, h.altitude as altitude, h.time_zone as time_zone, h.daylight_saving as daylight_saving, h.water_vapor as water_vapor, h.light_pollution as light_pollution," \
        "e.aperture as aperture, e.Fov as Fov, e.pixel_scale as pixel_scale, e.tracking_accuracy as accuracy, e.lim_magnitude as lim_magnitude, e.elevation_lim as elevation_lim," \
        "e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2, e.JohnsonB as JohnsonB, e.JohnsonR as JohnsonR, e.JohnsonV as JohnsonV, e.SDSSu as SDSSu," \
        "e.SDSSg as SDSSg, e.SDSSr as SDSSr, e.SDSSi as SDSSi,e.SDSSz as SDSSz, h.uhaveid as id" ,usr=usr).data()
    return user_equipments

def update_declination(uhaveid):
    query_relation = "MATCH (x:user)-[h:UhaveE{uhaveid:$uhaveid}]->(e:equipments) return h.longitude as longitude, h.latitude as latitude, h.altitude as altitude, e.elevation_lim as elevation_lim"
    eq_info = graph.run(query_relation, uhaveid=uhaveid).data()

    dec_lim = declination.run(float(eq_info[0]['longitude']), float(eq_info[0]['latitude']), float(eq_info[0]['altitude']), float(eq_info[0]['elevation_lim']))

    query_update = "MATCH (x:user)-[h:UhaveE{uhaveid:$uhaveid}]->(e:equipments) set h.declination_limit=$dec_lim"
    graph.run(query_update, uhaveid=uhaveid, dec_lim=dec_lim)


def delete_user_equipment(usr: str,uhaveid: int):
    #delete user's equipment
    graph.run("MATCH (x:user {email:$usr})-[h:UhaveE {uhaveid: $uhaveid}]->(e:equipments) DELETE h,e", usr=usr, uhaveid=uhaveid)


def create_user_target(usr: str, TID: int):
    query = "match (x:user{email:$usr}) match (t:target{TID:$TID}) create (x)-[ult:ULikeT{uliketid:uliketid}]->(t)"

    count = graph.run("MATCH ()-[ult:UlikeT]->() return ult.uliketid order by ult.uliketid DESC limit 1 ").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['ult.uliketid']+1

    graph.run(query, usr=usr, TID=TID, uliketid=cnt)


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
    equipment.camera_type1 = camera_type1
    equipment.camera_type2 = camera_typew
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
                           "e.tracking_accuracy as  tracking_accuracy, e.lim_magnitude as lim_magnotude, e.elevation_lim as elevation_lim, e.mount_type as mount_type, e.camera_type1 as camer_type1," \
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

def search_target(text: str):
    query= "MATCH (t:target) where t.name =~ $text return t.name as name order by t.name "
    target = graph.run(query, text = text).data()
    return target

def get_project_detail(PID: int):
    #get the project's detial
    query = "MATCH (n:project {PID: $PID})" \
    " return n.title as title, n.project_type as project_type, n.PI as PI, n.description as description, n.aperture_upper_limit as aperture_upper_limit, n.aperture_lower_limit as aperture_lower_limit," \
    "n.FoV_upper_limit as FoV_upper_limit, n.FoV_lower_limit as FoV_lower_limit, n.pixel_scale_upper_limit as pixel_scale_upper_limit, n.pixel_scale_lower_limit as pixel_scale_lower_limit," \
    "n.mount_type as mount_type, n.camera_type1 as camera_type1, n.camera_type2 as camera_type2, n.JohnsonB as JohnsonB, n.JohnsonR as JohnsonR, n.JohnsonV as JohnsonV, n.SDSSu as SDSSu," \
    "n.SDSSg as SDSSg, n.SDSSr as SDSSr, n.SDSSi as SDSSi, n.SDSSz as SDSSz, n.PID as PID"
    project = graph.run(query, PID = PID).data()
    return project

def get_project(usr: str)->Optional[Project]:
    # this function will return project which user can join
    query = "MATCH (x:user {email:$usr})-[rel:UhaveE]->(e:equipments) " \
        " return e.EID as EID,e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2,e.JohnsonB as jb,e.JohnsonV as jv, e.JohnsonR as jr, e.SDSSu as su, e.SDSSg as sg, e.SDSSr as sr , e.SDSSi as si, e.SDSSz as sz"
    equipment = graph.run(query, usr = usr).data()
    # print(equipment) 
    query = "MATCH (n:project) return n.title as title, n.project_type as project_type, n.PI as PI, n.description as description, n.aperture_upper_limit as aperture_upper_limit, n.aperture_lower_limit as aperture_lower_limit," \
        "n.FoV_upper_limit as FoV_upper_limit, n.FoV_lower_limit as FoV_lower_limit, n.pixel_scale_upper_limit as pixel_scale_upper_limit, n.pixel_scale_lower_limit as pixel_scale_lower_limit," \
        "n.mount_type as mount_type, n.camera_type1 as camera_type1, n.camera_type2 as camera_type2, n.JohnsonB as JohnsonB, n.JohnsonR as JohnsonR, n.JohnsonV as JohnsonV, n.SDSSu as SDSSu," \
        "n.SDSSg as SDSSg, n.SDSSr as SDSSr, n.SDSSi as SDSSi, n.SDSSz as SDSSz, n.PID as PID order by PID" 
    project = graph.run(query).data()
    result = []
    for i in range(len(equipment)):
        for j in range(len(project)):
            if apply_project_status(usr, project[j]['PID']) == 1:
                if any(d['PID'] == project[j]['PID'] for d in result): continue
                if equipment[i]['jb'] == 'n':
                    if project[j]['JohnsonB'] == 'y': continue
                if equipment[i]['jv'] == 'n':
                    if project[j]['JohnsonV'] == 'y': continue
                if equipment[i]['jr'] == 'n':
                    if project[j]['JohnsonR'] == 'y': continue
                if equipment[i]['su'] == 'n':
                    if project[j]['SDSSu'] == 'y': continue
                if equipment[i]['sg'] == 'n':
                    if project[j]['SDSSg'] == 'y': continue
                if equipment[i]['sr'] == 'n':
                    if project[j]['SDSSr'] == 'y': continue
                if equipment[i]['si'] == 'n':
                    if project[j]['SDSSi'] == 'y': continue
                if equipment[i]['sz'] == 'n':
                    if project[j]['SDSSz'] == 'y': continue
                if equipment[i]['mount_type'] != project[j]['mount_type']: continue
                if equipment[i]['camera_type1'] != project[j]['camera_type1']: continue
                if equipment[i]['camera_type2'] != project[j]['camera_type2']: continue
                n = graph.run("MATCH (x:user{email: $usr}) return x.name as manager_name",usr = usr).data()
                project[j]['manager_name'] = n[0]['manager_name']
                result.append(project[j]) 
        #query = "MATCH (x:user {email:$usr})-[rel:UhaveE]->(e:equipments), (n:project) where n.mount_type=e.mount_type and n.camera_type1=e.camera_type1 and n.camera_type2=e.camera_type2 " \
        #"and n.JohnsonB=e.JohnsonB and n.JohnsonV=e.JohnsonV and n.JohnsonR=e.JohnsonR  and n.SDSSu=e.SDSSu  and n.SDSSg=e.SDSSg and n.SDSSr=e.SDSSr and n.SDSSi=e.SDSSi and n.SDSSz=e.SDSSz" \
        #" return n.title as title, n.project_type as project_type, n.PI as PI, n.description as description, n.aperture_upper_limit as aperture_upper_limit, n.aperture_lower_limit as aperture_lower_limit," \
        #"n.FoV_upper_limit as FoV_upper_limit, n.FoV_lower_limit as FoV_lower_limit, n.pixel_scale_upper_limit as pixel_scale_upper_limit, n.pixel_scale_lower_limit as pixel_scale_lower_limit," \
        #"n.mount_type as mount_type, n.camera_type1 as camera_type1, n.camera_type2 as camera_type2, n.JohnsonB as JohnsonB, n.JohnsonR as JohnsonR, n.JohnsonV as JohnsonV, n.SDSSu as SDSSu," \
        #"n.SDSSg as SDSSg, n.SDSSr as SDSSr, n.SDSSi as SDSSi, n.SDSSz as SDSSz, n.PID as PID ORDER BY n.PID"
    #project = graph.run(query, usr = usr).data()
    return result

def get_project_target(pid: int):
    query = "MATCH x=(p:project{PID:$pid})-[r:PHaveT]->(t:target) RETURN t.name as name"
    project_target = graph.run(query, pid=pid).data()
    return project_target
    
def create_project(usr: str,title: str,project_type: str,description: str,aperture_upper_limit: float,aperture_lower_limit: float,FoV_upper_limit: float,
        FoV_lower_limit: float,pixel_scale_upper_limit: float,pixel_scale_lower_limit: float,mount_type: str,camera_type1: str,camera_type2: str,JohnsonB: str,
        JohnsonR: str,JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz: str)->Optional[Project]:
    #this function will create a project  
    count = graph.run("MATCH (p:project) return p.PID  order by p.PID DESC limit 1 ").data()
    project = Project()
    if len(count) == 0:
        project.PID = 0
    else:
        project.PID = count[0]['p.PID']+1
    project.title = title
    project.project_type = project_type
    tmp = graph.run("MATCH (x:user {email: $usr})  return x.UID", usr = usr).data()
    project.PI = tmp[0]['x.UID']
    project.description = description
    project.aperture_upper_limit = aperture_upper_limit
    project.aperture_lower_limit = aperture_lower_limit
    project.FoV_upper_limit = FoV_upper_limit
    project.FoV_lower_limit = FoV_lower_limit
    project.pixel_scale_upper_limit = pixel_scale_upper_limit
    project.pixel_scale_lower_limit = pixel_scale_lower_limit
    project.mount_type = mount_type
    project.camera_type1 = camera_type1
    project.camera_type2 = camera_type2
    project.JohnsonB = JohnsonB
    project.JohnsonR = JohnsonR
    project.JohnsonV = JohnsonV
    project.SDSSu = SDSSu
    project.SDSSg = SDSSg
    project.SDSSr = SDSSr
    project.SDSSi = SDSSi
    project.SDSSz = SDSSz
    graph.create(project)

    query= "MATCH (x:user {email: $usr}) MATCH (p:project {PID: $PID}) create (x)-[m:Manage {umanageid:$umanageid}]->(p)"
    count = graph.run("MATCH ()-[m:Manage]->() return m.umanageid  order by m.umanageid DESC limit 1 ").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['m.umanageid']+1
    graph.run(query, usr = usr, PID = project.PID, umanageid = cnt)
    return project

def upadte_project(usr: str,PID: int,umanageid: int,title: str,project_type: str,description: str,aperture_upper_limit: float,aperture_lower_limit: float,FoV_upper_limit: float,
        FoV_lower_limit: float,pixel_scale_upper_limit: float,pixel_scale_lower_limit: float,mount_type: str,camera_type1: str,camera_type2: str,JohnsonB: str,
        JohnsonR: str,JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz: str)->Optional[Project]:
    print(PID)
    print(umanageid)
    print(usr)
    query ="MATCH rel = (x:user)-[p:Manage {umanageid: $umanageid}]->(m:project) return rel"
    print(graph.run(query,usr = usr,umanageid = umanageid).data())
    query ="MATCH (x:user {email:$usr})-[p:Manage {umanageid: $umanageid}]->(m:project)" \
             f"SET m.title='{title}', m.project_type='{project_type}', m.description='{description}', m.aperture_upper_limit='{aperture_upper_limit}', m.aperture_lower_limit='{aperture_lower_limit}'," \
             f"m.FoV_upper_limit='{FoV_upper_limit}', m.FoV_lower_limit='{FoV_lower_limit}'," \
             f"m.pixel_scale_upper_limit='{pixel_scale_upper_limit}', m.pixel_scale_lower_limit='{pixel_scale_lower_limit}',"\
             f"m.mount_type='{mount_type}', m.camera_type1='{camera_type1}', m.camera_type2='{camera_type2}', m.JohnsonB='{JohnsonB}', m.JohnsonR='{JohnsonR}', m.JohnsonV='{JohnsonV}', " \
             f"m.SDSSu='{SDSSu}', m.SDSSg='{SDSSg}', m.SDSSr='{SDSSr}', m.SDSSi='{SDSSi}', m.SDSSz='{SDSSz}'"  
    project = graph.run(query,usr = usr, umanageid = umanageid)
    return project   

def delete_project(usr: str, PID: int, umanageid: int):
    graph.run("MATCH (x:user {email:$usr})-[m:Manage {umanageid: $umanageid}]->(p:project) DELETE m,p", usr=usr, umanageid = umanageid)


def get_project_manager_name(usr: str,PID: int):
    query = "MATCH (p:project {PID: $PID}) return p.PI as PI"
    result = graph.run(query,PID = PID).data()
    query = "MATCH (x:user {UID: $UID}) ,return x.name as name"
    manager_name = graph.run(query, UID = result[0]['PI']).data()
    return manager_name

def add_project_manager(usr: str, PID: int):
    query= "MATCH (x:user {email: $usr}) MATCH (p:project {PID: $PID}) create (x)-[m:Manage {umanageid:$umanageid}]->(p)"
    count = graph.run("MATCH ()-[m:Manage]->() return m.umanageid  order by m.umanageid DESC limit 1 ").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['m.umanageid']+1
    graph.run(query, usr = usr, PID = PID,umanageid = cnt)
    return

def user_manage_projects_get(usr: str):
    # return the project user manage 
    query="MATCH (x:user {email:$usr})-[m:Manage]->(p:project) return m.umanageid as umanageid, p.title as title, p.project_type as project_type," \
         "p.PI as PI, p.description as description, p.aperture_upper_limit as aperture_upper_limit, p.aperture_lower_limit as aperture_lower_limit," \
        "p.FoV_upper_limit as FoV_upper_limit, p.FoV_lower_limit as FoV_lower_limit, p.pixel_scale_upper_limit as pixel_scale_upper_limit, p.pixel_scale_lower_limit as pixel_scale_lower_limit," \
        "p.mount_type as mount_type, p.camera_type1 as camera_type1, p.camera_type2 as camera_type2, p.JohnsonB as JohnsonB, p.JohnsonR as JohnsonR, p.JohnsonV as JohnsonV, p.SDSSu as SDSSu," \
        "p.SDSSg as SDSSg, p.SDSSr as SDSSr, p.SDSSi as SDSSi, p.SDSSz as SDSSz, p.PID as PID "
    project = graph.run(query,usr = usr)
    return project

def create_project_target(usr: str, PID: int, TID: int, JohnsonB: str, JohnsonR: str, JohnsonV: str,SDSSu: str,SDSSg: str,SDSSr: str,SDSSi: str,SDSSz: str):
    query="MATCH (p:project {PID: $PID}) MATCH (t:target {TID:$TID}) create (p)-[pht:PHaveT" \
        " {phavetid:$phavetid, JohnsonB:$JohnsonB, JohnsonV:$JohnsonV, JohnsonR:$JohnsonR, SDSSu:$SDSSu, SDSSg:$SDSSg, SDSSr:$SDSSr, SDSSi:$SDSSi, SDSSz:$SDSSz}]->(t) return pht.phavetid "
    
    count = graph.run("MATCH ()-[pht:PHaveT]->() return pht.phavetid  order by pht.phavetid DESC limit 1 ").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['pht.phavetid']+1
    print(cnt)
    result = graph.run(query, PID = PID, TID = TID, phavetid = cnt, JohnsonB = JohnsonB, JohnsonR = JohnsonR, JohnsonV = JohnsonV, SDSSg = SDSSg, SDSSi = SDSSi, SDSSr = SDSSr, SDSSu = SDSSu, SDSSz = SDSSz).data()
    return result

def apply_project(usr: str,PID: int)->int:
    # this function will create an apply_to relationship to the project
    # return value
    # 1 : apply success

    query = "MATCH (x:user {email:$usr}) MATCH (p:project {PID:$PID})  create (x)-[:Apply_to {applyid: $applyid, status: $status, apply_time: $apply_time}]->(p)"
    time = graph.run("return datetime() as time").data() 
    count = graph.run("MATCH ()-[apply:Apply_to]->() return apply.applyid  order by apply.applyid DESC limit 1 ").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['apply.applyid']+1
    graph.run(query, usr = usr, PID = PID, applyid = cnt,status ='waiting', apply_time = time[0]['time'])
    return 1

def apply_project_status(usr: str, PID: int)->int:
    # this function will chechk whether user apply to the project or not 
    # 0 : error
    # 1 : no 
    # 2 : yes, waiting
    # 3 : yes, already join
    query = "MATCH (x:user {email:$usr})-[rel:Apply_to]->(p:project {PID:$PID}) return rel.status "
    result = graph.run(query, usr = usr, PID = PID).data()
    

    if len(result) == 0 or result[len(result)-1] == 'reject':
        return 1
    elif result[len(result)-1]['rel.status'] == 'accept':
        return 3
    elif result[len(result)-1]['rel.status'] == 'waiting':
        return 2
    else:
        return 0

def get_apply_waiting(usr: str):
    # this function will return the list of user's applied project which status is waiting
    query = "MATCH (x:user {email:$usr})-[:Apply_to {status: $status}]->(p:project) return p.PID as PID"
    waitiing_list = graph.run(query, usr = usr, status = 'waiting').data()
    return waitiing_list

def get_apply_history(usr: str):
     #this function will return the apply history of an user 
    query = "MATCH (x:user {email:$usr})-[rel:Apply_to]->(p:project) return p.PID as PID, rel.status as status, p.title as title, rel.apply_time as time"
    apply_history = graph.run(query, usr = usr).data()
    print(apply_history)
    return apply_history

def get_want_to_join_project(usr: str, PID : int):
    # project manage can get ther list of who want to join his project
    query = "MATCH (x:user)-[rel:Apply_to {status: $status}]->(p:project {PID: $PID}) return x.name as name, rel.applyid as applyid, rel.time as time "
    apply_list = graph.run(query, status = 'waiting', PID = PID).data()
    return apply_list

def reject_join_project(usr: str, PID: int, UID: int, applyid: int):
    # reject user'apply
    # 1 : success, 0: error
    query = "MATCH (x:user {email: $UID})-[rel:Apply_to {applyid: $applyid}]->(p:project {PID: $PID}) SET rel.status = $status return  rel.status as status"
    result = graph.run(query, status = 'reject', PID = PID, UID = UID, applyid = applyid).data()
    if len(result) == 1  and result[0]['status'] == 'reject':
        return 1
    else:
        return 0

def accept_join_project(usr: str, PID: int, UID: int, applyid: int):
    # accept user'apply
    query = "MATCH (x:user {email: $UID})-[rel:Apply_to {applyid: $applyid}]->(p:project {PID: $PID}) SET rel.status = $status return  rel.status as status"
    result = graph.run(query, status = 'accept', PID = PID, UID = UID, applyid = applyid).data()
    if len(result) == 1  and result[0]['status'] == 'accept':
        
        query = "CREATE (x:user {email: $UID})-[rel: Member_of {memberofid: $memberofid, join_time: $time}]->(p:project {PID: $PID})"
        count = graph.run("MATCH ()-[rel:Memberof]->() return rel.memberofif  order by rel.memberofid DESC limit 1 ").data()
        time = graph.run("return datetime() as time").data() 
        if len(count) == 0:
            cnt = 0
        else:
            cnt = count[0]['rel.memberofid']+1
        graph.run(query, UID = UID, PID =PID, memberofid = cnt, time = time[0]['time'])
        return 1
    else:
        return 0



def get_project_member(usr: str, PID: int):
    # return the user in this project
    query = "MATCH (x:user)-[rel:Member_of]->(p:project {PID: $PID}) return  x.name as name"
    member = graph.run(query, PID =PID).data()
    return member

def get_project_join(usr: str):
    #get all the project user have already joinied
    query = "MATCH (x:user {email:$usr})-[rel:Member_of]->(p:project) return p.PID as PID, p.title as title"
    join_list = graph.run(query, usr = usr).data()
    return  join_list

def get_project_join_filter(projectlist: list,usr: str,uhaveid: int):

    print(uhaveid)
    equipment = graph.run("MATCH (x:user{email: $usr})-[:UhaveE{uhaveid:$uhaveid}]->(e:equipments) " \
        " return e.EID as EID,e.JohnsonB as jb,e.JohnsonV as jv, e.JohnsonR as jr, e.SDSSu as su, e.SDSSg as sg, e.SDSSr as sr , e.SDSSi as si, e.SDSSz as sz" \
        ",e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2" ,usr = usr , uhaveid = uhaveid).data()
    print(equipment) 
    result = []
    for j in range(len(projectlist)):
            if projectlist[j]['PID'] in result: continue
            
            p = get_project_detail(projectlist[j]['PID'])
            
            if equipment[0]['jb'] == 'n':
                if p[0]['JohnsonB'] == 'y': continue
            if equipment[0]['jv'] == 'n':
                if p[0]['JohnsonV'] == 'y': continue
            if equipment[0]['jr'] == 'n':
                if p[0]['JohnsonR'] == 'y': continue
            if equipment[0]['su'] == 'n':
                if p[0]['SDSSu'] == 'y': continue
            if equipment[0]['sg'] == 'n':
                if p[0]['SDSSg'] == 'y': continue
            if equipment[0]['sr'] == 'n':
                if p[0]['SDSSr'] == 'y': continue
            if equipment[0]['si'] == 'n':
                if p[0]['SDSSi'] == 'y': continue
            if equipment[0]['sz'] == 'n':
                if p[0]['SDSSz'] == 'y': continue
            if equipment[0]['mount_type'] != p[0]['mount_type']: continue
            if equipment[0]['camera_type1'] != p[0]['camera_type1']: continue
            if equipment[0]['camera_type2'] != p[0]['camera_type2']: continue
            result.append(projectlist[j])

    return result


def fliter_project_target(usr: str, PID: int):
    #return the target based on user's equipment 
    query = "MATCH (x:user {email:$usr})-[rel:UhaveE]->(e:equipments) " \
        " return e.EID as EID,e.mount_type as mount_type, e.camera_type1 as camera_type1, e.camera_type2 as camera_type2,e.JohnsonB as jb,e.JohnsonV as jv, e.JohnsonR as jr, e.SDSSu as su, e.SDSSg as sg, e.SDSSr as sr , e.SDSSi as si, e.SDSSz as sz, rel.declination_limit as declination"
    equipment = graph.run(query, usr = usr).data()
    #query = "MATCH (x:user {email:$usr})-[rel:UhaveE]->(e:equipments), (n:project {PID: $PID}) where n.mount_type=e.mount_type and n.camera_type1=e.camera_type1 and n.camera_type2=e.camera_type2 " \
    #   "and n.JohnsonB=e.JohnsonB and n.JohnsonV=e.JohnsonV and n.JohnsonR=e.JohnsonR  and n.SDSSu=e.SDSSu  and n.SDSSg=e.SDSSg and n.SDSSr=e.SDSSr and n.SDSSi=e.SDSSi and n.SDSSz=e.SDSSz" \
    #    " return e.EID as EID,e.JohnsonB as jb,e.JohnsonV as jv, e.JohnsonR as jr, e.SDSSu as su, e.SDSSg as sg, e.SDSSr as sr , e.SDSSi as si, e.SDSSz as sz"
    #equipment = graph.run(query, usr = usr, PID = PID).data()
    project_target = graph.run("MATCH (p:project {PID: $PID})-[pht:PHaveT]->(t:target) " \
        " return pht.JohnsonB as JohnsonB, pht.JohnsonV as JohnsonV, pht.JohnsonR as JohnsonR, pht.SDSSu as SDSSu, pht.SDSSg as SDSSg, pht.SDSSr as SDSSr , pht.SDSSi as SDSSi, pht.SDSSz as SDSSz"
    ", t.TID as TID, t.name as name, t.latitude as dec", PID = PID).data()
    print(len(equipment))
    print(len(project_target))
    target = []
    # filter with equipment capability
    for i in range(len(equipment)):
        for j in range(len(project_target)):
            if any(d['TID'] == project_target[j]['TID'] for d in target): continue
            if equipment[i]['jb'] == 'n':
                if project_target[j]['JohnsonB'] == 'y': continue
            if equipment[i]['jv'] == 'n':
                if project_target[j]['JohnsonV'] == 'y': continue
            if equipment[i]['jr'] == 'n':
                if project_target[j]['JohnsonR'] == 'y': continue
            if equipment[i]['su'] == 'n':
                if project_target[j]['SDSSu'] == 'y': continue
            if equipment[i]['sg'] == 'n':
                if project_target[j]['SDSSg'] == 'y': continue
            if equipment[i]['sr'] == 'n':
                if project_target[j]['SDSSr'] == 'y': continue
            if equipment[i]['si'] == 'n':
                if project_target[j]['SDSSi'] == 'y': continue
            if equipment[i]['sz'] == 'n':
                if project_target[j]['SDSSz'] == 'y': continue
            # filter with equipment declination limit
            if float(equipment[i]['declination']) <= 0 and float(project_target[j]['dec']) < float(equipment[i]['declination']):
                continue
            if float(equipment[i]['declination']) > 0 and float(project_target[j]['dec']) > float(equipment[i]['declination']):
                continue

            target.append(project_target[j])
    print(len(target))

    return target


def create_schedule(eid: int, uhaveid: int):
    # get EID
    # EID = get_eid(uhaveid)

    count = graph.run("MATCH (s:schedule) return s.SID order by s.SID DESC limit 1").data()
    schedule = Schedule()
    if len(count) == 0:
        schedule.SID = 0
    else:
        schedule.SID = count[0]['s.SID']+1
    
    # schedule.date #Y:M:D

    # get nighttime
    observe_section, current_time = get_night_time(uhaveid)

    schedule.observe_section = observe_section
    schedule.last_update = str(current_time)
    graph.create(schedule)
    print(eid)
    query="MATCH (e:equipments {EID: $EID}) MATCH (s:schedule {SID: $SID}) CREATE (e)-[r:EhaveS {ehavesid:$ehavesid}]->(s)"
    count = graph.run("MATCH ()-[r:EhaveS]->() return r.ehavesid  order by r.ehavesid DESC limit 1").data()
    if len(count) == 0:
        cnt = 0
    else:
        cnt = count[0]['r.ehavesid']+1

    graph.run(query, EID=eid, SID=schedule.SID, ehavesid=cnt)

    # return schedule


def load_schedule(uhaveid: int):
    # find the equipment
    EID = get_eid(uhaveid)

    # if the equipment doesn't have a schedule, create one!
    query_count_schedule = "MATCH (e:equipments{EID:$EID})-[r:EhaveS]->(s:schedule) RETURN count(r) as cnt"
    result_count = graph.run(query_count_schedule, EID=EID).data()
    if result_count[0]['cnt'] == 0:
        create_schedule(EID, uhaveid)

    # get nighttime
    new_observe_section, current_time = get_night_time(uhaveid)

    # find the schedule
    query_schedule = "MATCH (e:equipments{EID:$EID})-[r:EhaveS]->(s:schedule) return s.observe_section as observe_section s.last_update as last_update"
    result = graph.run(query_schedule, EID=EID).data()
    old_observe_section = result[0]['observe_section']
    previous_time = result[0]['last_update']

    # calculate the updated schedule
    updated_schedule = [-1]*24
    format = '%Y-%m-%d %H:%M:%S'
    gap = current_time - datetime.strptime(previous_time, format)
    if len(str(gap)) > 10:
        updated_schedule = new_observe_section
    else:
        start_index = int(str(gap).split(":")[0])
        j = start_index
        for i in range(24):
            if j < 24:
                updated_schedule[i] = old_observe_section[j]
                j+=1
            else:
                updated_schedule[i] = new_observe_section[i]

    # return the new calculated schedule to front-end
    return updated_schedule



def save_schedule(usr: str):
    pass


def get_eid(uhaveid):
    query_eid = "MATCH (x:user)-[h:UhaveE{uhaveid:$uhaveid}]->(e:equipments) return e.EID as EID"
    eid = graph.run(query_eid, uhaveid=uhaveid).data()

    eid = int(uhid[0]['EID'])

    return eid


def get_observable_time(usr: str, uhaveid: int, tid_list: list):
    # hour array
    hour = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"]
    # get current time for further calculation
    current_time = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)
    current_time_sec = str(current_time).split('.')[0]
    current_hour = current_time_sec.split(" ")[1].split(":")[0]

    # create current hour array
    index = hour.index(current_hour)
    current_hour_array = []
    for i in range(24):
        current_hour_array.append(hour[index])
        if index == 23:
            index = 0
        else:
            index += 1
    print(current_hour_array)
    
    # get information from uhavee and equipment table
    query_relation = "MATCH (x:user)-[h:UhaveE{uhaveid:$uhaveid}]->(e:equipments) return h.longitude as longitude, h.latitude as latitude, h.altitude as altitude, e.elevation_lim as elevation_lim"
    eq_info = graph.run(query_relation, uhaveid=uhaveid).data()

    longitude = float(eq_info[0]['longitude'])
    latitude = float(eq_info[0]['latitude'])
    altitude = float(eq_info[0]['altitude'])
    elevation_lim = float(eq_info[0]['elevation_lim'])

    # get target information and run the ta's schedule function
    format = '%Y-%m-%d %H:%M:%S'
    # tid_list = [856, 266, 377, 488, 5, 100, 348, 7]

    target_data = []
    for i in range(len(tid_list)):
        # create observation array
        observe = [0]*24

        query_target = "match (t:target) where t.TID=$tid return t.TID as TID, t.name as name, t.longitude as ra, t.latitude as dec"
        tar_info = graph.run(query_target, tid=tid_list[i]['TID']).data()

        tid = int(tar_info[0]['TID'])
        ra = float(tar_info[0]['ra'])
        dec = float(tar_info[0]['dec'])
        name = str(tar_info[0]['name'])

        t_start, t_end = schedule.run(uhaveid, longitude, latitude, altitude, elevation_lim, tid, ra, dec, current_time)
        #print('start observation: %s \nend observation %s' % (t_start, t_end))

        if str(t_start) != 'nan' and str(t_end)  != 'nan':
            t1 = str(t_start).split('.')[0].replace("T", " ")
            t2 = str(t_end).split('.')[0].replace("T", " ")

            time_left2start = datetime.strptime(t1, format) - datetime.strptime(current_time_sec, format)
            time_left2end = datetime.strptime(t2, format) - datetime.strptime(current_time_sec, format)
            # print('time left to start: ', time_left2start)
            # print('time_left to end:   ', time_left2end)

            o1 = int(str(time_left2start).split(":")[0])
            o2 = int(str(time_left2end).split(":")[0])+1
            for j in range(24):
                if j >= o1-1 and j < o2:
                    observe[j] = 1
            t_data = {'TID':tid_list[i]['TID'], 'name':name, 'start':t1.split(" ")[1], 'end':t2.split(" ")[1], 'time_section':observe, 'hour':current_hour_array}
        #else:
            #observe = [0]*24
            #t_data = {'TID':tid_list[i], 'name':name, 'start':str(t_start), 'end':str(t_end), 'time_section':observe, 'hour':current_hour_array}

            target_data.append(t_data)
        #print(t_data)

    return target_data


def get_night_time(uhaveid):
    query_eq = "MATCH (x:user)-[r:UhaveE{uhaveid:$uhaveid}]->(e:equipments) RETURN r.longitude as longitude, r.latitude as latitude, r.altitude as altitude"
    eq_info = graph.run(query_eq, uhaveid=uhaveid).data()

    longitude = str(eq_info[0]['longitude'])
    latitude = str(eq_info[0]['latitude'])
    altitude = float(eq_info[0]['altitude'])

    try:
        observe_section, current_time = night.night(longitude, latitude, altitude)
    except ephem.NeverUpError:
        observe_section = [-1]*24
    except ephem.AlwaysUpError:
        observe_section = [-2]*24
    
    return observe_section, current_time
