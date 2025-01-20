import json
from Lib.SwimDataHolder import MeetHeaderDisplay,HeatDataDisplay,SwimerBoardDetail
class JsonHelper:
    def GetJSONFromFile(ReadJsonPath):
        with open(ReadJsonPath,"r") as f:
            data= json.load(f)
        return	data

    def SetJSONToFile (data,WriteJsonPath):
        with open(WriteJsonPath,"w") as f:
             json.dump(data,f)		
        return	
        #VCR TBD Remove unwanted '/'
        #{"MeetDetail":"{\"MeetName\": \"Name of the Event\", \"MeetDate\": \" eventAddressss\", \"MeetAddress\": \" eventAddressss\"}"}
    def GetMeetHeader(data):
        meetHeaderDisplay= MeetHeaderDisplay()
        meetHeaderDisplay.MeetName= data["MeetName"]
        meetHeaderDisplay.MeetDate= data["MeetDate"]
        meetHeaderDisplay.MeetAddress= data["MeetAddress"]
        sjson= json.dumps(meetHeaderDisplay.__dict__)
       #  xx= ord('/')
#         y = chr(xx)
        print (sjson)
        return sjson

        # TBD
    def GetNextHeatIDFromFile(data):
        for event in data["EventDetails"]:
            for Heat in event["HeatList"]:
                if (Heat["HeatStartTime"]=="0" and Heat["HeatEndTime"]=="0"):
                    print(Heat["HeatID"])
                    return Heat["HeatID"]
        return 0

    # Update Swimmer time to heat List File
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
                        for time in timeings:
                            if Board["BoardID"] == str(time.boardId):
                                Board["SwimTimings"]=time.timerValue
                                print (Board["SwimTimings"])
                                break

        return


    # Get Swimmer List From Heat List
    def GetHeatDataDisplay(heatID, data):
        heatDataDisplay= HeatDataDisplay()
        swimerBoardDetails=[]
        for event in data["EventDetails"]:
            heatDataDisplay.eventID=event["eventID"]
            heatDataDisplay.eventName=event["eventName"]
            for Heat in event["HeatList"]:
                if (Heat["HeatID"]==heatID):				
                    heatDataDisplay.HeatID=Heat["HeatID"]
                    heatDataDisplay.HeatStartTime=Heat["HeatStartTime"]
                    heatDataDisplay.HeatEndTime=Heat["HeatEndTime"]
                    for Board in Heat["BoardList"]:
                        swimerBoardDetail= SwimerBoardDetail(Board["BoardID"],Board["SwimerName"],Board["SwimerID"],0,0,0,0,0,0)
                        swimerBoardDetails.append(swimerBoardDetail)
                    heatDataDisplay.SwimerBoardDetails= swimerBoardDetails
                    print(str(heatDataDisplay.SwimerBoardDetails[0].swimmername))
                    return heatDataDisplay
        return

# JSONFilePath= "/home/pks/Desktop/Pi-py Web Server/Data/MeetDetails.json"
# data= JsonHelper.GetJSONFromFile(JSONFilePath)
#JsonHelper.GetMeetHeader(data)
#JsonHelper.GetHeatDataDisplay(data)
# HeatID= JsonHelper.GetNextHeatFromFile(data)
# if (HeatID!=""):
#     JsonHelper.GetHeatDataDisplay(HeatID,data)