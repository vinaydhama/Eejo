from urllib.request import urlopen 
import json 
class FireBaseHelper:
    url = "https://eejo-managerdb-default-rtdb.firebaseio.com//EventDetails.json"
    def DownloadFirebaseToLocal(url):
        response = urlopen(url)   
        data_json = json.loads(response.read()) 
        # print(data_json) 
        with open("C:\\Users\\vchikkay\\Documents\\Arduino\\NodeMCU\\NODEMCU_IO\\data.json", 'w') as f:
            json.dump(data_json, f)

    # Update Swimmer time to heat List File
    def setHeatResultstoFirebase(heatID, HeatStartTime,HeatEndTime,data, timeings ):
        eventID=-1
        HeatID=-1
        url= "https://eejo-managerdb-default-rtdb.firebaseio.com/EventDetails/"
        for event in range(0,len(data)):            
            for heat in range(0,len (data[event]["HeatList"])):
                if (heatID==data[event]["HeatList"][heat]["HeatID"]):
                    eventID= event
                    HeatID= heat
                    break
            if ( eventID!=-1):
                url = "https://eejo-managerdb-default-rtdb.firebaseio.com/EventDetails/"+ str(eventID)+ "/HeatList/"+str(HeatID)
                # print (str(eventID))
                # print (str(HeatID))
                print (url)
                print (json.dumps(data[eventID]["HeatList"][HeatID]))
                break
        return url
JSONFilePath= "C:\\Users\\vchikkay\\Documents\\Arduino\\NodeMCU\\NODEMCU_IO\\data.json"
data= ""
print(data)
url = FireBaseHelper.setHeatResultstoFirebase("50_FSB2",100,200,data,{1,2,3,4,5})
print(url)
