const fs = require('fs');
const fetch = require('node-fetch'); // Ensure you have node-fetch installed
const Logger = require('./Lib/LoggerService'); // Adjust the path to your Logger
const ChangeInfo = require('./Lib/SwimDataHolder').Changeinfo; // Adjust as necessary

class FireBaseHelper {
    static SwimmerTable = "";
    static MeetID = "meetID";
    static FirebaseJsonData = "";
    static MeetNumber = 1;
    static parentPath = __dirname + '/../..'; // Adjust according to your project structure
    static FirebaseJSONFilePath = `${FireBaseHelper.parentPath}/Data/FirebaseJSONData_Local.json`;
    static FirebaseSwimmerTable = `${FireBaseHelper.parentPath}/Data/FirebaseSwimmerTable.json`;
    static WriteHeatResultsPath = `${FireBaseHelper.parentPath}/Data/HeatExecutionResult.json`;
    static strJson = ".json";
    static EventBaseUrl = `https://eejo-managerdb-default-rtdb.firebaseio.com/Meets/${FireBaseHelper.MeetNumber}/EventDetails`;
    static SwimmerURL = "https://eejo-managerdb-default-rtdb.firebaseio.com/Swimmers";
    
    static ChangenidentifiedforFirebase = [];

    static async createIfFileDoesNotExist(filePath) {
        try {
            if (!fs.existsSync(filePath)) {
                fs.writeFileSync(filePath, ""); // Create an empty file
                return true;
            }
            return true; // File already exists
        } catch (ex) {
            Logger.app_log.error("Exception occurred in createIfFileDoesNotExist:", ex);
        }
        return false;
    }

    static async internetOn() {
        try {
            const response = await fetch('http://www.tinytechniques.com', { timeout: 5000 });
            return response.ok;
        } catch (ex) {
            Logger.app_log.error("Exception occurred in internetOn:", ex);
        }
        return false;
    }

    static async loadSwimmerTableToFile(url, filePath) {
        if (await FireBaseHelper.internetOn() && await FireBaseHelper.createIfFileDoesNotExist(filePath)) {
            try {
                const response = await fetch(url);
                FireBaseHelper.SwimmerTable = await response.json();
                fs.writeFileSync(filePath, JSON.stringify(FireBaseHelper.SwimmerTable, null, 2)); // Pretty printing
            } catch (ex) {
                Logger.app_log.error("Exception occurred in loadSwimmerTableToFile:", ex);
            }
            return FireBaseHelper.SwimmerTable;
        }
        return false;
    }

    static generateTimeUpdateListsForFirebase(localData, firebaseData) {
        if (localData != null && firebaseData != null) {
            for (let event = 0; event < localData.length; event++) {
                for (let heat = 0; heat < localData[event].HeatList.length; heat++) {
                    for (let board = 0; board < localData[event].HeatList[heat].BoardList.length; board++) {
                        if (localData[event].HeatList[heat].BoardList[board].SwimTimings !== firebaseData[event].HeatList[heat].BoardList[board].SwimTimings) {
                            FireBaseHelper.ChangenidentifiedforFirebase.push(new ChangeInfo(event, heat, board, localData[event].HeatList[heat].BoardList[board].SwimTimings, 0));
                        }

                        if (localData[event].HeatList[heat].BoardList[board].SwimmerID !== firebaseData[event].HeatList[heat].BoardList[board].SwimmerID) {
                            FireBaseHelper.ChangenidentifiedforLocal.push(new ChangeInfo(event, heat, board, 1, 0));
                        }
                    }
                }
            }
            return FireBaseHelper.ChangenidentifiedforFirebase, FireBaseHelper.ChangenidentifiedforLocal
        }
        return;
    }

    static async appendHeatResult(appendJsonPath, dataToUpdate) {
        try {
            fs.appendFileSync(appendJsonPath, JSON.stringify(dataToUpdate) + "\n");
        } catch (ex) {
            Logger.app_log.error("Exception occurred in appendHeatResult:", ex);
        }
    }

    static async updateHeatResultToFirebase(updatedHeatData, heatIndex, eventIndex) {
        if (await FireBaseHelper.internetOn()) {
            let url = `${FireBaseHelper.EventBaseUrl}/${eventIndex}/HeatList/${heatIndex}.json`;
            const data = JSON.stringify(updatedHeatData);
            await fetch(url, { method: 'PATCH', body: data });
        }
    }

    // Additional methods similar to your provided Python implementation can be added here

}

// Example usage
(async () => {
    const url = 'https://example.com/swimmerdata'; // Change to actual URL
    const filePath = FireBaseHelper.FirebaseSwimmerTable;
    const swimmerTable = await FireBaseHelper.loadSwimmerTableToFile(url, filePath);
    console.log(swimmerTable);
})();