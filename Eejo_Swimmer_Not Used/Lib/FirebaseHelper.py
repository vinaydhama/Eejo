from urllib.request import urlopen
import requests
import json
from Lib.LogerService import Logger
class FireBaseHelper:
    JsonFilepath ="/home/pks/Desktop/Pi-py Web Server/Data/FirebaseJSONData.json"
    url = "https://eejo-managerdb-default-rtdb.firebaseio.com//EventDetails.json"
    def DownloadFirebaseToLocal(url,Filepath):
        try:
            response = urlopen(url)
            data_json = json.loads(response.read())
            # print(data_json)
            with open(Filepath, 'w') as f:
                json.dump(data_json, f)

        except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return

    def PostJSONRequesttoFireeBase(url,jsonobj):
        try:

            urlBoardlist= url+ "/BoardList"+".json"
            print (urlBoardlist)
            print (jsonobj.BoardList)

            x= requests.post(urlBoardlist,json = jsonobj.BoardList)

            print(x.text)


        except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)

    # Update Swimmer time to heat List File
    def setHeatResultstoFirebase(HeatOrderID,EventOrderID,jsonstr):
        try:
    #        baseurl= "https://eejo-managerdb-default-rtdb.firebaseio.com/EventDetails/"
            url = "https://eejo-managerdb-default-rtdb.firebaseio.com/EventDetails/"+ str(HeatOrderID)+ "/HeatList/"+str(EventOrderID)
           #  print (url)
#             print(jsonstr)
            FireBaseHelper.PostJSONRequesttoFireeBase(url,jsonstr)
        except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return

       #* for event in range(0,len(data)):
        #    for heat in range(0,len (data[event]["HeatList"])):
        #        if (heatID==data[event]["HeatList"][heat]["HeatID"]):
        #            eventID= event
        #            HeatID= heat
        #            break
        #    if ( eventID!=-1):
        #        url = "https://eejo-managerdb-default-rtdb.firebaseio.com/EventDetails/"+ str(eventID)+ "/HeatList/"+str(HeatID)
        #        print (url)
        #        jsonstr= json.dumps(data[eventID]["HeatList"][HeatID])
        #        FireBaseHelper.PostJSONRequesttoFireeBase(url,jsonstr)
        #        print (jsonstr)
        #        break */
        #
        #return url

        # Update Swimmer time to heat List File
    def setHeatResultstoLocalJSONDB(HeatIDToUpdate,EventIDToUpdate,heatDataDisplay,data):
        try:
            for eventID in range(0,len(data)):
                if (data[eventID]["eventID"]==EventIDToUpdate):
                    for heat in range(0,len (data[eventID]["HeatList"])):
                        if (HeatIDToUpdate==data[eventID]["HeatList"][heat]["HeatID"]):
                            print("HeatID" + data[eventID]["HeatList"][heat]["HeatID"])

                            data[eventID]["HeatList"][heat]["HeatStartTime"]= heatDataDisplay.HeatStartTime
                            data[eventID]["HeatList"][heat]["HeatEndTime"]= heatDataDisplay.HeatEndTime
                            print (data[eventID]["HeatList"][heat]["HeatStartTime"])
                            print(data[eventID]["HeatList"][heat]["HeatEndTime"])

                            for Board in range(0,len (data[eventID]["HeatList"][heat]["BoardList"])):
                                data[eventID]["HeatList"][heat]["BoardList"][Board]["SwimTimings"]=heatDataDisplay.SwimerBoardDetails[Board].timerValue
                                print (data[eventID]["HeatList"][heat]["BoardList"][Board]["SwimTimings"])
                            jsonstr= data[eventID]["HeatList"][heat]
#                            jsonstr=""
                            return jsonstr, heat, eventID

                return data,-1,-1

                            #for time in heatDataDisplay.SwimerBoardDetails:
                            #    if Board["BoardID"] == time.boardId:
                            #        Board["SwimTimings"]=time.timerValue
                            #        Logger.app_log.info("Writing to Board "+ str(time.boardId)+ " Raw Latched Value @" + str(time.timerValue))
                            #        #print (Board["SwimTimings"])
                            #return               #break


        except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return

    def GetJSONFromFile(ReadJsonPath):
        with open(ReadJsonPath,"r") as f:
            data= json.load(f)
        return	data

#FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.url,FireBaseHelper.JsonFilepath)
#data= FireBaseHelper.GetJSONFromFile(FireBaseHelper.JsonFilepath)
##print(data)
#heatDataDisplay= ""
#Updateddata, HeatID, eventID= FireBaseHelper.setHeatResultstoLocalJSONDB("50_FSB2","50_FS_G06_B",heatDataDisplay,data)
#
#FireBaseHelper.setHeatResultstoFirebase( HeatID, eventID,Updateddata)

#print(Updateddata)
#FireBaseHelper.PostJSONRequesttoFireeBase("