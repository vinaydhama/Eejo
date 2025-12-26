import requests
import json
import time 

url1 = 'http://localhost:5002/SetNextHeatDetails'
url2 = 'http://localhost:5002/SetEventDetails'

ReadJsonPath="/home/pks/Desktop/Pi-py Web Server/datafile.json"
WriteJsonPath="/home/pks/Desktop/Pi-py Web Server/datafile1.json"



myobjtest= [{ "A": "sas"},{   "B": "sasa"}]
    

myobj1 = {
    "MeetName": "Name of the Event",
    "MeetDate": " eventAddressss",
    "MeetAddress": " eventAddressss",
    "eventName": "Boys G-5 50m FS",
    "HeatID": "0",
    "HeatStartTime": "0",
    "HeatEndTime": "0",
    "heatBoardDetailsList": [
        {
            "SwimerID": "0",
            "SwimerName": "SwimerName0",
            "SwimStatus": "0",
            "SwimTimings": "122"
        },
        {
            "SwimerID": "1",
            "SwimerName": "SwimerName1",
            "SwimStatus": "0",
            "SwimTimings": "120"
        },
        {
            "SwimerID": "2",
            "SwimerName": "SwimerName2",
            "SwimStatus": "0",
            "SwimTimings": "121"
        }
    ]
}


DisplayJson = {
    "eventName" : "Python",
    "framework" : "Flask",
    "website" : "Scotch",
    "version_info" : {
        "python" : "3.9.0",
        "flask" : "1.1.2"
    },
    "examples" : ["query", "form", "json"],
    "boolean_test" : "true"
}



myobj2= {
    "MeetName": "Name of the Event",
    "MeetDate": " eventAddressss",
    "MeetAddress": " eventAddressss",
    "lastProcessedHeatDetails": "EVEID:HeatID",
    "GroupDetails": [
        {
            "Year": "2000",
            "GroupName": "Group-1"
        },
        {
            "Year": "2001",
            "GroupName": "Group-2"
        }
    ],
    "EventDetails": [
        {
            "eventID": "evebid1",
            "eventName": "eventName01",            
            "HeatList": [
                {
                    "HeatID": "0",
                    "HeatStartTime": "0",
                    "HeatEndTime": "0",
                    "BoardList": [
                        {                        
                            "SwimerID": "0",
                            "SwimerName": "SwimerName0",
                            "SwimStatus": "0",
                            "SwimTimings": "122"
                        },
                        {
                            "SwimerID": "1",
                            "SwimerName": "SwimerName1",
                            "SwimStatus": "0",
                            "SwimTimings": "120"
                        },
                        {
                            "SwimerID": "2",
                            "SwimerName": "SwimerName2",
                            "SwimStatus": "0",
                            "SwimTimings": "121"
                        }
                    ]
                },
                {
                    "HeatID": "2",
                    "HeatStartTime": "0",
                    "HeatEndTime": "0",
                    "BoardList": [
                        {
                            "SwimerID": "0",
                            "SwimerName": "SwimerName0",
                            "SwimStatus": "0",
                            "SwimTimings": "122"
                        },
                        {
                            "SwimerID": "1",
                            "SwimerName": "SwimerName1",
                            "SwimStatus": "0",
                            "SwimTimings": "120"
                        },
                        {
                            "SwimerID": "2",
                            "SwimerName": "SwimerName2",
                            "SwimStatus": "0",
                            "SwimTimings": "121"
                        }
                    ]
                }
            ]
        }
    ]
}


def GetJSONFromFile(ReadJsonPath):
	with open(ReadJsonPath,"r") as f:
		data= json.load(f)
#		data= str(data).replace("\'", "\"")
#		print (data)
	return	data

def SetJSONToFile (data,WriteJsonPath):
	with open(WriteJsonPath,"w") as f:
		 json.dump(data,f)		
	return	

# Update Swimmer time to heat List
def setHeatResults(heatID, HeatStartTime,HeatEndTime,data, timeings ):

	for event in data["EventDetails"]:
		for Heat in event["HeatList"]:			
			print(Heat["HeatID"])
			if (Heat["HeatID"]==heatID):			
				Heat["HeatStartTime"]= HeatStartTime
				Heat["HeatEndTime"]= HeatEndTime
				print (Heat["HeatStartTime"])
				print(Heat["HeatEndTime"])
			#print (Heat)					
				for Board in Heat["BoardList"]:
					if Board["BoardID"] in timeings:
						Board["SwimTimings"]=timeings[Board["BoardID"]]
						print (Board["SwimTimings"])						
						return 
	return 
		

# Get Swimmer List From Heat List
def GetHeatDetails(heatID, data):
	SwimmerList = {}
	for event in data["EventDetails"]:
		for Heat in event["HeatList"]:
			if (Heat["HeatID"]==heatID):				
				for Board in Heat["BoardList"]:
					SwimmerList.update({Board["BoardID"]: Board["SwimerName"]})
				return SwimmerList
					
	return SwimmerList

data = GetJSONFromFile(ReadJsonPath)
setHeatResults("2",time.time(),time.time()+10,data,{"0":"110","1":"111","2":"212"})
print (GetHeatDetails("2",data))
SetJSONToFile(data,WriteJsonPath)

