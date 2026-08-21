console.log("home_user.js has loaded!");

function OpenAccountmanage() {
    document.getElementById("popup").style.display = "block";
}

function CloseAccountmanage() {
    document.getElementById("popup").style.display = "none";
}

document.addEventListener("click", function(event) {
    const popup = document.getElementById("popup")
    const accountLink = document.getElementById("accountpopup");

    if (!popup.contains(event.target) && event.target != accountLink){
        CloseAccountmanage();
    }
});

function testButton(button) {
    console.log("BUTTON WORKED");
    console.log(button.dataset.itemId);
    console.log(button.dataset.itemAmount);
}