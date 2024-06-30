var deliveriesAdded = false; 
var requests_file;

var locations, deliveries, costList, revenueList, profit_list;
var basePrice, loadingRate, kilometerPrice, kilometerCost;
var priceModel;

const RED = '#ffc3b3';
const GREEN = '#e1ffc7';
const ORANGE = '#ffd8b1';
const GRAY = '#F3F3F3';

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

    if(color == "green") {
        message.style.backgroundColor = GREEN;
    }

    if(color == "red") {
        message.style.backgroundColor = RED;
    }

    if(color == "orange") {
        message.style.backgroundColor = ORANGE;
    }

    if(color == "gray") {
        message.style.backgroundColor = GRAY;
    }
    
    var messageText = document.createElement('p');
    var formattedText = input.replace(/\n/g, '<br>')
    messageText.textContent = `(${getTime()}) ${formattedText}`;

    message.appendChild(messageText);
    chatLog.appendChild(message);

    chatLog.scrollTop = chatLog.scrollHeight; 
}

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

    priceModel = {
        basePrice: document.getElementById("basePrice").value,
        loadingRate: document.getElementById("loadingRate").value,
        kilometerPrice: document.getElementById("kilometerPrice").value,
        kilometerCost: document.getElementById("kilometerCost").value,
        sell_threshold: document.getElementById("sell_threshold").value,
        buy_threshold: document.getElementById("buy_threshold").value
    };

    fetch('/generate_deliveries', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(priceModel)
    })
    .then(response => response.json())
    .then(data => {
        locations = data.locations;
        deliveries = data.deliveries;
        revenueList = data.revenueList;
        costList = data.costList;
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

    // Check if deliveries are added
    if(!deliveriesAdded)
    {
        errorMessage.textContent = "Add deliveries.";
        return false;
    }

    errorMessage.textContent = "";
    return true;
}

function registerAuction() {
    if(!checkInputError()) {
        return;
    }

    regButton = document.getElementById("registerButton");
    blkBackground = document.getElementById("chatBlkBackground");
    companyTitle = document.getElementById("companyTitle");
    companyName = document.getElementById("companyName");

    companyTitle.textContent = companyName.value;
    companyName.style.display = "none";
    blkBackground.style.display = "none";
    companyTitle.style.display = "block";
    regButton.style.display = "none";

    initCarrier(companyName.value);
}

function showActionDisplay() {
    document.getElementById("actionDisplay").style.display = "block";
    document.getElementById("actionDarkBG").style.display = "block";
}

function closeActionDisplay() {
    document.getElementById("actionDisplay").style.display = "none";
    document.getElementById("actionDarkBG").style.display = "none";
}

//#region Carrier
function initCarrier(companyName) {
    const socket = io();

    socket.on('connect', () => {
        
        socket.on(companyName, (data) => {
            let action = data["action"]
            
            if(action == "log") {
                sendMessage(data.message, "gray");
            }
            else if(action == "register") {
                handleRegister(data["payload"]["status"]);
            }
            else if(action == "request_offer") {
                handleRequests(data["payload"]);
            }
            else if(action == "bid") {
                handleBid(data["payload"]);
            }
            else if(action == "request_auction_results") {
                handleAuctionResult(data["payload"], companyName);
            }
            else if(action == "confirm") {
                handleConfirm(data["payload"]);
            }
        });

        fetch('/init_carrier', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                companyName: companyName, 
                locations: locations, 
                revenues: revenueList, 
                costs: costList, 
                profits: profitList,
                basePrice: priceModel['basePrice'],
                loadingRate: priceModel['loadingRate'],
                kilometerPrice: priceModel['kilometerPrice'],
                kilometerCost: priceModel['kilometerCost'],
                sell_threshold: priceModel['sell_threshold'],
                buy_threshold: priceModel['buy_threshold'] 
            })
        });
    });
}

function handleRegister(status) {
    if(status == "OK") {
        sendMessage("Registered for auction!", "green");
        return;
    }

    if(status == "NO_REGISTRATION_PHASE") {
        sendMessage("Error: Auctioneer is not in registration phase!", "red");
        return;
    }

    if(status == "ALREADY_REGISTERED") {
        sendMessage("Error: The carrier id is already registered!", "red");
        return;
    }
}

function handleRequests(payload) {
    if(payload["status"] == "OK") {
        let p_x = payload["offer"]["loc_pickup"]["pos_x"];
        let p_y = payload["offer"]["loc_pickup"]["pos_y"];
        let d_x = payload["offer"]["loc_dropoff"]["pos_x"];
        let d_y = payload["offer"]["loc_dropoff"]["pos_y"];

        let minPrice = payload["offer"]["min_price"];
        let revenue = payload["offer"]["revenue"];
        
        let offeror = payload["offer"]["offeror"];

        sendMessage(`Current Auction: (${p_x}, ${p_y}) -> (${d_x}, ${d_y}) | Minimum price: ${minPrice} | Revenue: ${revenue} | Offer by ${offeror}`, "orange");
        return;
    }
    
    if(payload["status"] == "OFFER_REQUEST_TIMEOUT") {
        sendMessage("Error: the request timed out!", "red");
        return;
    }
    
    if(payload["status"] == "NO_OFFERS_AVAILABLE") {
        sendMessage("Error: There are currently no offers available!", "red");
        return;
    }

    if(payload["status"] == "NOT_REGISTERED") {
        sendMessage("Error: The carrier is not registered for the auction!", "red");
        return;
    }
}

function handleBid(payload) {
    if(payload["status"] == "OK") {
        sendMessage(`Bid`, "gray");
        return;
    }
    
    if(payload["status"] == "BIDDING_TIMEOUT") {
        sendMessage("Error: Bidding request timed out!", "red");
        return;
    }
    
    if(payload["status"] == "INVALID_BID") {
        sendMessage("Error: There bid was invalid!", "red");
        return;
    }

    if(payload["status"] == "NOT_REGISTERED") {
        sendMessage("Error: The carrier is not registered for the auction!", "red");
        return;
    }
}

function handleAuctionResult(payload, carrierId) {
    if(payload["status"] == "OK") {
        let winner = payload["offer"]["winner"];
        let winningBid = payload["offer"]["winning_bid"];
        
        if(winner == carrierId) {
            sendMessage(`The winner of the auction is ${winner} for ${winningBid}€`, "green");
            return;
        }

        if(winner == "NONE") {
            sendMessage(`There is not winner for the auction.`, "red");
            return;
        }

        sendMessage(`The winner of the auction is ${winner} for ${winningBid}€`, "red");
        return;
    }
    
    if(payload["status"] == "NO_RESULTS_AVAILABLE") {
        sendMessage("Error: There are no results available!", "red");
        return;
    }
    
    if(payload["status"] == "NO_RESULTS_PHASE") {
        sendMessage("Error: The auctioneer is not in a result phase!", "red");
        return;
    }

    if(payload["status"] == "NOT_REGISTERED") {
        sendMessage("Error: The carrier is not registered for the auction!", "red");
        return;
    }
}

function handleConfirm(payload) {
    if(payload["status"] == "OK") {
        sendMessage("The result has been confirmed!", "gray");
        return;
    }
    
    if(payload["status"] == "NO_CONFIRMATION_AVAILABLE") {
        sendMessage("Error: There was no confirmation!", "red");
        return;
    }
    
    if(payload["status"] == "CONFIRMATION_TIMEOUT") {
        sendMessage("Error: The comfirmation timed out!", "red");
        return;
    }

    if(payload["status"] == "NOT_REGISTERED") {
        sendMessage("Error: The carrier is not registered for the auction!", "red");
        return;
    }
}
//#endregion


//#region Auctioneer
function startServer() {
    document.getElementById("auctioneerChat").style.display = "flex";
    document.getElementById("serverButton").style.display = "none";
    document.getElementById("auctionBlkBackground").style.display = "none";

    initAuctioneer();
}

function initAuctioneer() {
    const socket = io();

    socket.on('connect', () => {
        socket.on('auctioneer_log', (data) => {
            sendMessage(data.message, "gray");
        });

        socket.on('auctioneer', (data) => {
            if(data["action"] == "addAuction") {
                createAuction(data["payload"]);
            }
            else if(data["action"] == "addBid") {
                handleBid(data);
            }
            else if(data["action"] == "addResult") {
                handleResult(data);
            }
            else if(data["action"] == "end") {
                handleAuctionEnd();
            }
        });

        fetch('/init_auctioneer', {
            
        })
        
    });
} 

function handleBid(data) {
    sendMessage(data.message, "orange");

    var auctionStatusDiv = document.getElementById(data["payload"]["offerId"]);
    auctionStatusDiv.textContent = "Bidding...";

    var auctionDivParent = auctionStatusDiv.parentNode.parentNode;
    auctionDivParent.style.backgroundColor = "#f1b04c";
}

function handleResult(data) {
    var winner = data["payload"]["winner"];
    var auctionStatusDiv = document.getElementById(data["payload"]["offer_id"]);
    var auctionDivParent = auctionStatusDiv.parentNode.parentNode;
    
    if(winner == "NONE") {
        sendMessage("There is no winner for the request", "red");
        auctionStatusDiv.textContent = "No winner";
        auctionDivParent.style.backgroundColor = RED;
    }
    else {
        sendMessage("Winner of the auction is " + winner, "green");
        auctionStatusDiv.textContent = "Winner: " + winner;
        auctionDivParent.style.backgroundColor = GREEN;
    }
}

function handleAuctionEnd() {
    sendMessage("Auction day closed. Restart server for new auctions.", "red");
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
    var auctionId = document.createElement('div');
    
    var auctionStatus = document.createElement('div');
    auctionStatus.classList.add('auctionStatus');
    auctionStatus.setAttribute('id', input["offerId"]);

    logText.style.backgroundColor = "#CCCCCC";

    chatLog.appendChild(logText);
    
    logText.appendChild(textSection1);

    logText.appendChild(divider);

    logText.appendChild(textSection2);

    auctionTitle.textContent = `(${input["pickup"]["pos_x"]}, ${input["pickup"]["pos_y"]}) -> (${input["dropoff"]["pos_x"]}, ${input["dropoff"]["pos_y"]})`;
    auctionInfo.textContent = `Min Price: ${input["minPrice"]}€, Revenue: ${input["revenue"]}€`;
    auctionId.textContent = `ID: ${input["offerId"]}`;
    textSection1.appendChild(auctionTitle);
    textSection1.appendChild(auctionInfo);
    textSection1.appendChild(auctionId);
    
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
//#endregion


//#region Simulation
function sendConsole(input, agentID, color) {
    var console = document.getElementById(agentID);

    var message = document.createElement('p');
    message.classList.add('message', 'sent');

    if(color == "green") {
        message.style.backgroundColor = "#e1ffc7";
    }

    if(color == "red") {
        message.style.backgroundColor = "#ffdbc7";
    }
    
    var messageText = document.createElement('p');
    messageText.textContent = `(${getTime()}) ${input}`;

    message.appendChild(messageText);
    console.appendChild(message);

    console.scrollTop = console.scrollHeight; 
}

function startSimulation() {
    let carrierAmount = parseInt(document.getElementById("carrierAmount").value);

    let simulButton = document.getElementById("simulButton");
    simulButton.style.backgroundColor = "gray";
    simulButton.textContent = "Simulating...";

    let consoleContainer = document.getElementById("consoleContainer");
    consoleContainer.innerHTML = ''; // Clear previous contents

    let totalConsoles = carrierAmount + 1; // Total consoles to instantiate
    let consoleRow;

    for (let i = 0; i < totalConsoles; i++) {
        // Create a new row for every two consoles
        if (i % 2 === 0) {
            consoleRow = document.createElement('div');
            consoleRow.classList.add('consoleRow');
        }

        var consolet = document.createElement('div');
        var consoleTitle = document.createElement('div');
        var consoleChat = document.createElement('div');

        if (i === 0) {
            consolet.classList.add('consoles');
            consoleTitle.classList.add('consoleTitle');
            consoleTitle.textContent = `Auctioneer`;
            consoleChat.id = "auctioneerSim";
            consoleChat.classList.add('consoleChat');
        } else {
            consolet.classList.add('consoles');
            consoleTitle.classList.add('carrierConsoleTitle');
            consoleTitle.textContent = `Carrier ${i}`;
            consoleChat.id = `Carrier ${i}`;
            consoleChat.classList.add('consoleChat');
        } 

        consolet.appendChild(consoleTitle);
        consolet.appendChild(consoleChat);
        consoleRow.appendChild(consolet);

        // Add empty console if odd amount of carriers
        if (i === totalConsoles - 1 && totalConsoles % 2 === 1) {
            var consolet = document.createElement('div');
            var consoleTitle = document.createElement('div');
            var consoleChat = document.createElement('div');
            consolet.classList.add('consoles'); // Different class for the extra console
            consoleTitle.classList.add('consoleTitle'); // Different class for the title
            consoleTitle.textContent = `Extra`;
            consoleChat.classList.add('consoleChat'); // Different class for the chat
            consolet.appendChild(consoleTitle);
            consolet.appendChild(consoleChat);
            consoleRow.appendChild(consolet);
        }

        // Append the row to the container when it's full 
        if (i % 2 === 1 || (i === totalConsoles - 1)) {
            consoleContainer.appendChild(consoleRow);
        }

        
    }

    // initAuctioneer();

    startCarriers(totalConsoles);
}

function startCarriers(totalConsoles) {
    for (let i = 1; i < totalConsoles; i++) {
        setTimeout(() => {
            initCarrier(`Carrier ${i}`);
        }, i * 1000); // 1000 milliseconds delay between each initialization
    }
}

//#endregion