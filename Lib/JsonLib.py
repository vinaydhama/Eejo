import json
from Lib.SwimDataHolder import MeetHeaderDisplay,HeatDataDisplay,SwimerBoardDetail
from Lib.LogerService import Logger
class JsonHelper:

    def AppendHeatResult(AppendJsonPath,dataToUpdate):
        with open(AppendJsonPath, "a+") as json_file:
            json_file.write("{}\n".format(json.dumps(dataToUpdate)))
        return

    # def GetJSONFromFile(ReadJsonPath):
    #     with open(ReadJsonPath,"r") as f:
    #         data= json.load(f)
    #     return	data

    # def SetJSONToFile (data,WriteJsonPath):
    #     with open(WriteJsonPath,"w") as f:
    #          json.dump(data,f)		
    #     return	
        #VCR TBD Remove unwanted '/'
        #{"MeetDetail":"{\"MeetName\": \"Name of the Event\", \"MeetDate\": \" eventAddressss\", \"MeetAddress\": \" eventAddressss\"}"}
    def GetMeetHeader(data):
        meetHeaderDisplay= MeetHeaderDisplay()
        meetHeaderDisplay.MeetName= data[0]["MeetName"]
        meetHeaderDisplay.MeetDate= data[0]["MeetDate"]
        meetHeaderDisplay.MeetAddress= data[0]["MeetAddress"]
        sjson= json.dumps(meetHeaderDisplay.__dict__)
        print (sjson)
        return sjson

        # TBD
    def GetNextHeatIDFromFile(data):
        # for eventID in range(0,len(data['EventDetails'])):

        for eventID in range(0,len(data['EventDetails'])):
            for heat in range(0,len (data['EventDetails'][eventID]["HeatList"])):
                heatdata = data['EventDetails'][eventID]["HeatList"][heat]
                if (heatdata["HeatStartTime"]==11111111111111 and heatdata["HeatEndTime"]==11111111111111):
                    return heatdata["HeatID"],data['EventDetails'][eventID]["eventID"]


        #for event in data[0]:
        #    for Heat in data[0]event["HeatList"]:
        #        if (Heat["HeatStartTime"]==0 and Heat["HeatEndTime"]==0):
        #            print(Heat["HeatID"])
        #            return Heat["HeatID"],event["eventID"]
        return 0,0


    def GetAllHeatIDsFromFile(data):
            # for eventID in range(0,len(data['EventDetails'])):
        HeatIds=[]

        for eventID in range(0,len(data['EventDetails'])):
            for heat in range(0,len (data['EventDetails'][eventID]["HeatList"])):
                heatdata = data['EventDetails'][eventID]["HeatList"][heat]
                HeatIds.append(heatdata["HeatID"])
        return HeatIds
    # Update Swimmer time to heat List File
    #NOT USED
    # def setHeatResults(heatID,EventID, heatDataDisplay ,data):

    #    for event in data:
    #        if (event["eventID"]==EventID):
    #            for Heat in event["HeatList"]:			
    #                print(Heat["HeatID"])
    #                if (Heat["HeatID"]==heatID):			
    #                    Heat["HeatStartTime"]= heatDataDisplay.HeatStartTime
    #                    Heat["HeatEndTime"]= heatDataDisplay.HeatEndTime
    #                    print (Heat["HeatStartTime"])
    #                    print(Heat["HeatEndTime"])
    #                #print (Heat)					
    #                    for Board in Heat["BoardList"]:
    #                        for time in heatDataDisplay.SwimerBoardDetails:
    #                            if Board["BoardID"] == time.boardId:
    #                                Board["SwimTimings"]=time.timerValue
    #                                Logger.app_log.info("Writing to Board "+ str(time.boardId)+ " Raw Latched Value @" + str(time.timerValue))
    #                                #print (Board["SwimTimings"])
    #                    return               #break

    #    return

    def updateJsonFile(AppendJsonPath,dataToUpdate):
        jsonFile = open(AppendJsonPath, "r") # Open the JSON file for reading
        data = json.load(jsonFile) # Read the JSON into the buffer
        jsonFile.close() # Close the JSON file

        ## Working with buffered content
        tmp = data["location"]
        data["location"] = path
        data["mode"] = "replay"

        ## Save our changes to JSON file
        jsonFile = open(AppendJsonPath, "w+")
        jsonFile.write(json.dumps(data))
        jsonFile.close()


    # Get Swimmer List From Heat List to Timer start
    def GetHeatDataDisplay(heatIDToDisplay,EventIDToDisplay, data):
        heatDataDisplay= HeatDataDisplay()
        swimerBoardDetails=[]
        for eventID in range(0,len(data['EventDetails'])):
#             if (data[eventID]["eventID"]==EventIDToDisplay):
                EventHolder = data['EventDetails'][eventID]
                heatDataDisplay.eventID=EventHolder["eventID"]
                heatDataDisplay.eventName=EventHolder["eventName"]
                for heat in range(0,len (EventHolder["HeatList"])):			
                   # print(EventHolder["HeatList"][heat]["HeatID"])
                    if (EventHolder["HeatList"][heat]["HeatID"]==heatIDToDisplay):
                        heatDataDisplay.HeatStartTime = EventHolder["HeatList"][heat]["HeatStartTime"]
                        heatDataDisplay.HeatEndTime = EventHolder["HeatList"][heat]["HeatEndTime"]
                        heatDataDisplay.HeatID=heatIDToDisplay
                        for Board in range(0,len (EventHolder["HeatList"][heat]["BoardList"])):
                            swimerBoardDetails.append(SwimerBoardDetail(EventHolder["HeatList"][heat]["BoardList"][Board]["BoardID"],EventHolder
                            ["HeatList"][heat]["BoardList"][Board]["SwimerName"],EventHolder["HeatList"][heat]["BoardList"][Board]
                            ["SwimerID"],0,EventHolder["HeatList"][heat]["BoardList"][Board]["SwimStatus"],0,0,0,0,0))
                            #swimerBoardDetails.append(SwimerBoardDetail(Board["BoardID"],Board["SwimerName"],Board["SwimerID"],0,Board["SwimStatus"],0,0,0,0))
                        heatDataDisplay.SwimerBoardDetails= swimerBoardDetails
                        return heatDataDisplay



       # for event in data:
       #     heatDataDisplay.eventID=event["eventID"]
       #     heatDataDisplay.eventName=event["eventName"]
       #     for Heat in event["HeatList"]:
       #         if (Heat["HeatID"]==heatID):				
       #             heatDataDisplay.HeatID=heatID
       #             heatDataDisplay.HeatStartTime=Heat["HeatStartTime"]
       #             heatDataDisplay.HeatEndTime=Heat["HeatEndTime"]
       #             for Board in Heat["BoardList"]:
       #                 swimerBoardDetails.append(SwimerBoardDetail(Board["BoardID"],Board["SwimerName"],Board["SwimerID"],0,Board["SwimStatus"],0,0,0,0))
       #             heatDataDisplay.SwimerBoardDetails= swimerBoardDetails
       #             return heatDataDisplay
       # return