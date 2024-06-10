var deliveriesAdded = false;
var locations, profit_list;

function uploadDeliveries() {
    const fileInput = document.getElementById('file');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload_deliveries', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        locations = data.locations;
        deliveries = data.deliveries;
        profitList = data.profitList;
        document.getElementById("frameGUI").src = 'data:image/png;base64,' + data.plot;
        document.getElementById("revenue").textContent = data.revenueTotal;
        document.getElementById("cost").textContent = data.cost;
        document.getElementById("profit").textContent = data.profit;
        document.getElementById("distance").textContent = data.distance;
        closeActionDisplay();
        showPlot();
        deliveriesAdded = true;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function generateDeliveries() {
    fetch('/generate_deliveries')
        .then(response => response.json())
        .then(data => {
            locations = data.locations;
            deliveries = data.deliveries;
            profitList = data.profitList;
            document.getElementById("frameGUI").src = 'data:image/png;base64,' + data.plot;
            document.getElementById("revenue").textContent = data.revenueTotal;
            document.getElementById("cost").textContent = data.cost;
            document.getElementById("profit").textContent = data.profit;
            document.getElementById("distance").textContent = data.distance;
            closeActionDisplay();
            showPlot();
            deliveriesAdded = true;
        })
        .catch(error => console.error('Error:', error));
}

function showPlot() {
    document.getElementById("darkBackground").style.display = "none";
    document.getElementById("deliveryButton").style.display = "none";
    document.getElementById("frameGUI").style.display = "block";
    document.getElementById("guiTitle").style.display = "block";
}

function checkInputError() {
    errorMessage = document.getElementById("errorMessage");
    
    // Check for company name
    if(document.getElementById("companyName").value === "")
    {
        errorMessage.textContent = "Enter company name.";
        document.getElementById("companyName").style.border = "2px solid red";
        return false;
    }

    // Check for min value out of range
    if(document.getElementById("minVal").value === "")
    {
        errorMessage.textContent = "Min value out of bounds.";
        return false;
    }

    // Check for max value out of range
    if(document.getElementById("maxVal").value === "")
    {
        errorMessage.textContent = "Max value out of bounds.";
        return false;
    }

    // Check if deliveries are added
    if(!deliveriesAdded)
    {
        errorMessage.textContent = "Add deliveries.";
        return false;
    }

    errorMessage.style.display = "none";
    return true;
}

function registerAuction() {
    if(!checkInputError())
    {
        return;
    }

    chat = document.getElementById("carrierChat");
    regButton = document.getElementById("registerButton");
    settings = document.getElementById("settings");
    companyTitle = document.getElementById("companyTitle");
    companyName = document.getElementById("companyName").value

    companyTitle.textContent = companyName;
    companyTitle.style.display = "block";
    minVal = document.getElementById("minVal").value;
    maxVal = document.getElementById("maxVal").value;
    settings.style.display = "none";
    regButton.style.display = "none";
    chat.style.display = "flex";

    initCarrier(companyName);
}

function showActionDisplay() {
    document.getElementById("actionDisplay").style.display = "block";
    document.getElementById("actionDarkBG").style.display = "block";
}

function closeActionDisplay() {
    document.getElementById("actionDisplay").style.display = "none";
    document.getElementById("actionDarkBG").style.display = "none";
}

function getTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const currentTime = `${hours}:${minutes}:${seconds}`;
    return currentTime;
}

function sendMessage(input, color) {
    var chatLog = document.getElementById('chatLog');
    var chatInput = document.getElementById('chatInput');

    var message = document.createElement('div');
    message.classList.add('message', 'sent');

    if(color == "green")
    {
        message.style.backgroundColor = "#e1ffc7";
    }

    if(color == "red")
    {
        message.style.backgroundColor = "#ffdbc7";
    }
    
    var messageText = document.createElement('p');
    messageText.textContent = `(${getTime()}) ${input}`;

    message.appendChild(messageText);
    chatLog.appendChild(message);

    chatLog.scrollTop = chatLog.scrollHeight; 
}

function startServer() {
    document.getElementById("auctioneerChat").style.display = "flex";
    document.getElementById("serverButton").style.display = "none";

    initAuctioneer();
}

function initAuctioneer() {
    const socket = io();

    socket.on('connect', () => {
        socket.on('auctioneer_log', (data) => {
            sendMessage(data.message, "green");
        });

        socket.on('auctioneer_offers', (data) => {
            sendMessage(data.message, "red");
        });

        fetch('/init_auctioneer', {
            
        })
        
    });
} 

function initCarrier(companyName) {
    const socket = io();

    socket.on('connect', () => {
        
        socket.on("carrier_log", (data) => {
            sendMessage(data.message, "green");
        });

        socket.on("carrier_error", (data) => {
            sendMessage(data.message, "red");
        });

        fetch('/init_carrier', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ companyName: companyName, locations: locations, profitList: profitList })
        })
    });
}


function createAuction(input) {
    var chatLog = document.getElementById('auctionLog');

    var logText = document.createElement('div');
    logText.classList.add('auctionLogText');

    var textSection1 = document.createElement('div');
    textSection1.classList.add('auctionLogTextSections');

    var divider = document.createElement('div');
    divider.classList.add('auctionLogTextDivider');

    var textSection2 = document.createElement('div');
    textSection2.classList.add('auctionLogTextSections');

    var auctionTitle = document.createElement('div');
    auctionTitle.classList.add('auctionTitle');

    var auctionInfo = document.createElement('div');
    
    var auctionStatus = document.createElement('div');
    auctionStatus.classList.add('auctionStatus');

    logText.style.backgroundColor = "#CCCCCC";

    chatLog.appendChild(logText);
    
    logText.appendChild(textSection1);

    auctionTitle.textContent = `.`;
    logText.appendChild(divider);

    logText.appendChild(textSection2);

    auctionTitle.textContent = `Request ${input}`;
    auctionInfo.textContent = `(x, y) -> (x, y), Revenue: ${input}`;
    textSection1.appendChild(auctionTitle);
    textSection1.appendChild(auctionInfo);
    
    auctionStatus.textContent = "Waiting...";
    textSection2.appendChild(auctionStatus);
    
    logText.appendChild(messageText);

    // chatLog.scrollTop = chatLog.scrollHeight; 
}

function biddingAuction(input) {
    var chatLog = document.getElementById('auctionLog');

    var logText = document.createElement('div');
    logText.classList.add('auctionLogText');

    var textSection1 = document.createElement('div');
    textSection1.classList.add('auctionLogTextSections');

    var divider = document.createElement('div');
    divider.classList.add('auctionLogTextDivider');

    var textSection2 = document.createElement('div');
    textSection2.classList.add('auctionLogTextSections');

    var auctionTitle = document.createElement('div');
    auctionTitle.classList.add('auctionTitle');

    var auctionInfo = document.createElement('div');
    
    var auctionStatus = document.createElement('div');
    auctionStatus.classList.add('auctionStatus');

    if(color == "green")
    {
        logText.style.backgroundColor = "#e1ffc7";
    }

    if(color == "red")
    {
        logText.style.backgroundColor = "#ffdbc7";
    }
    if(color == "orange")
    {
        logText.style.backgroundColor = "#FDAE44";
    }
    if(color == "gray")
    {
        logText.style.backgroundColor = "#CCCCCC";
    }

    chatLog.appendChild(logText);
    
    logText.appendChild(textSection1);

    auctionTitle.textContent = `.`;
    logText.appendChild(divider);

    logText.appendChild(textSection2);

    auctionTitle.textContent = `Request ${input}`;
    auctionInfo.textContent = `(x, y) -> (x, y), Revenue: ${input}`;
    textSection1.appendChild(auctionTitle);
    textSection1.appendChild(auctionInfo);
    
    auctionStatus.textContent = "Waiting...";
    textSection2.appendChild(auctionStatus);
    
    logText.appendChild(messageText);

    // chatLog.scrollTop = chatLog.scrollHeight; 
}