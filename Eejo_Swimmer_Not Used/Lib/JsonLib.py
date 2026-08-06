import json
from Lib.SwimDataHolder import MeetHeaderDisplay,HeatDataDisplay,SwimerBoardDetail
from Lib.LogerService import Logger
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
        meetHeaderDisplay.MeetName= data[0]["MeetName"]
        meetHeaderDisplay.MeetDate= data[0]["MeetDate"]
        meetHeaderDisplay.MeetAddress= data[0]["MeetAddress"]
        sjson= json.dumps(meetHeaderDisplay.__dict__)
        print (sjson)
        return sjson

        # TBD
    def GetNextHeatIDFromFile(data):
        for eventID in range(0,len(data)):
                for heat in range(0,len (data[eventID]["HeatList"])):
                    if (data[eventID]["HeatList"][heat]["HeatStartTime"]==0 and data[eventID]["HeatList"][heat]["HeatEndTime"]==0):
                        return data[eventID]["HeatList"][heat]["HeatID"],data[eventID]["eventID"]


        #for event in data[0]:
        #    for Heat in data[0]event["HeatList"]:
        #        if (Heat["HeatStartTime"]==0 and Heat["HeatEndTime"]==0):
        #            print(Heat["HeatID"])
        #            return Heat["HeatID"],event["eventID"]
        return 0,0

    # Update Swimmer time to heat List File
    #NOT USED
    #def setHeatResults(heatID,EventID, heatDataDisplay ,data):
    #
    #    for event in data["EventDetails"]:
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
    #
    #    return


    # Get Swimmer List From Heat List to Timer start
    def GetHeatDataDisplay(heatIDToDisplay,EventIDToDisplay, data):

        heatDataDisplay= HeatDataDisplay()
        swimerBoardDetails=[]
        for eventID in range(0,len(data)):
            if (data[eventID]["eventID"]==EventIDToDisplay):
                heatDataDisplay.eventID=EventIDToDisplay
                heatDataDisplay.eventName=data[eventID]["eventName"]
                for heat in range(0,len (data[eventID]["HeatList"])):			
                    print(data[eventID]["HeatList"][heat]["HeatID"])
                    if (data[eventID]["HeatList"][heat]["HeatID"]==heatIDToDisplay):
                        heatDataDisplay.HeatStartTime = data[eventID]["HeatList"][heat]["HeatStartTime"]
                        heatDataDisplay.HeatEndTime = data[eventID]["HeatList"][heat]["HeatEndTime"]
                        heatDataDisplay.HeatID=heatIDToDisplay
                        for Board in range(0,len (data[eventID]["HeatList"][heat]["BoardList"])):
                            swimerBoardDetails.append(SwimerBoardDetail(data[eventID]["HeatList"][heat]["BoardList"][Board]["BoardID"],data[eventID]
                            ["HeatList"][heat]["BoardList"][Board]["SwimerName"],data[eventID]["HeatList"][heat]["BoardList"][Board]
                            ["SwimerID"],0,data[eventID]["HeatList"][heat]["BoardList"][Board]["SwimStatus"],0,0,0,0))
                            #swimerBoardDetails.append(SwimerBoardDetail(Board["BoardID"],Board["SwimerName"],Board["SwimerID"],0,Board["SwimStatus"],0,0,0,0))
                        heatDataDisplay.SwimerBoardDetails= swimerBoardDetails
                        return heatDataDisplay



       # for event in data["EventDetails"]:
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