let baseURL = 'http://' + GetEejoHostID() + ':5002';
let MeetingID = 1;
let TableCreated = false;
let HeatSetURL = baseURL + '/SetNextHeat';
let cmdurl = baseURL + '/SetLiveHeatCommands?';
let GetHeatsURL = 'GetAllHeatIDsFromFile';

// Fetch heat list dynamically
async function fetchAndUpdateHeatList(apiUrl) {
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        const heatSelector = document.getElementById('HeatSelector');
        heatSelector.innerHTML = '';
        data.commandReturnData.forEach(heatName => {
            const option = document.createElement('option');
            option.value = heatName;
            option.text = heatName;
            heatSelector.add(option);
        });
    } catch (error) {
        console.error('Error fetching heat list:', error);
    }
}

function ExecuteLiveCmd(CmdToSend, CmdDict) {
    switch (CmdToSend) {
        case 'SetNextHeat':
            CmdToSend = 'CmdName=SetNextHeat&HeatName=' + CmdDict;
            break;
        case 'AutoFindHeat':
            CmdToSend = 'CmdName=AutoFindHeat&AutoCmd=' + CmdDict;
            break;
        case 'Start': CmdToSend = 'CmdName=HeatCommand&HeatCmdValue=1'; break;
        case 'Pause': CmdToSend = 'CmdName=HeatCommand&HeatCmdValue=2'; break;
        case 'Stop': CmdToSend = 'CmdName=HeatCommand&HeatCmdValue=3'; break;
        case 'Complete': CmdToSend = 'CmdName=HeatCommand&HeatCmdValue=4'; break;
        case 'SwimmerNameDispCmd':
            CmdToSend = `CmdName=SwimmerNameDispCmd&SwBoardID=${CmdDict.SwBoardID}&SwNameValue=${CmdDict.SwNameValue}`;
            break;
        case 'SwimmerTimeDispCmd':
            CmdToSend = `CmdName=SwimmerTimeDispCmd&SwBoardID=${CmdDict.SwBoardID}&SwTimeValue=${convertToSeconds(CmdDict.SwTimeValue)}`;
            break;
        case 'SwimmerStatusCmd':
            CmdToSend = `CmdName=SwimmerStatusCmd&SwBoardID=${CmdDict.SwBoardID}&SwStatusCmdValue=${CmdDict.SwStatusCmdValue}`;
            break;
        case 'BoardTimerCmd':
            CmdToSend = `CmdName=BoardTimerCmd&SwBoardID=${CmdDict.SwBoardID}&BoardTimerCmdValue=${CmdDict.BoardTimerCmdValue}`;
            break;
    }
    if (CmdToSend) SendLiveCmd(CmdToSend);
}

async function SendLiveCmd(CmdtoSend) {
    try {
        const urlToFetch = cmdurl + CmdtoSend;
        const response = await fetch(urlToFetch);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

function convertToSeconds(timeStr) {
    const parts = timeStr.split(':').map(Number);
    return parts.length === 2 ? parts[0] * 60 + parts[1] : Number(timeStr);
}

function tableCreate(NoOfBoard) {
    const tbl = document.getElementById('Tab1');
    tbl.innerHTML = '';
    tbl.insertAdjacentHTML('beforeend', `<thead class='table-dark'>
        <tr><th colspan='4' class='fs-3'>MEET NAME</th></tr>
        <tr><td class='fs-6'>Heat: 123</td><td class='fs-6'>Address</td><td class='fs-6'>Dec 2024</td><td></td></tr>
    </thead>`);

    tbl.insertAdjacentHTML('beforeend', `<tr><td colspan='4'>
        <select id='HeatSelector' class='form-select mb-2'></select>
        <select id='HeatCmd' class='form-select mb-2'>
            <option value=''>Select Command</option>
            <option value='Start'>Start</option>
            <option value='Stop'>Stop</option>
            <option value='Complete'>Complete</option>
        </select>
    </td></tr>`);

    document.getElementById('HeatSelector').addEventListener('change', e => {
        ExecuteLiveCmd(e.target.value ? 'SetNextHeat' : 'AutoFindHeat', e.target.value || '1');
    });
    document.getElementById('HeatCmd').addEventListener('change', e => {
        if (e.target.value) ExecuteLiveCmd(e.target.value);
    });

    for (let i = 0; i < NoOfBoard; i++) {
        const rowHTML = `<tr>
            <td>${i + 1}</td>
            <td><input type='text' id='SwName${i}' class='form-control mb-2' placeholder='Swimmer Name'></td>
            <td><input type='text' id='TimerDisp${i}' class='form-control mb-2' placeholder='Enter Time'></td>
            <td>
                <select id='SwStatus${i}' class='form-select mb-2'>
                    <option value='0'></option><option value='1'>AB</option><option value='2'>DQ</option><option value='3'>DNC</option>
                </select>
                <select id='BoardCmd${i}' class='form-select mb-2'>
                    <option value='0'></option><option value='1'>Stop</option><option value='2'>Continue</option><option value='3'>Disable</option><option value='4'>Bypass</option>
                </select>
            </td>
        </tr>`;
        tbl.insertAdjacentHTML('beforeend', rowHTML);

        document.getElementById(`SwName${i}`).addEventListener('keyup', e => {
            if (e.key === 'Enter') ExecuteLiveCmd('SwimmerNameDispCmd', { SwBoardID: i, SwNameValue: e.target.value });
        });
        document.getElementById(`TimerDisp${i}`).addEventListener('keyup', e => {
            if (e.key === 'Enter') ExecuteLiveCmd('SwimmerTimeDispCmd', { SwBoardID: i, SwTimeValue: e.target.value });
        });
        document.getElementById(`SwStatus${i}`).addEventListener('change', e => {
            if (e.target.value !== '0') ExecuteLiveCmd('SwimmerStatusCmd', { SwBoardID: i, SwStatusCmdValue: e.target.value });
        });
        document.getElementById(`BoardCmd${i}`).addEventListener('change', e => {
            if (e.target.value !== '0') ExecuteLiveCmd('BoardTimerCmd', { SwBoardID: i, BoardTimerCmdValue: e.target.value });
        });
    }
}

window.onload = () => {
    tableCreate(10);
    fetchAndUpdateHeatList(cmdurl + 'CmdName=' + GetHeatsURL);
};
