// function for clicking account link
function OpenAccountmanage() {
    //displays pop up by using id and changing css
    document.getElementById("popup").style.display = "block";
}

//function when closing the pop-up
function CloseAccountmanage() {
    //hides pop-up
    document.getElementById("popup").style.display = "none";
}

// function which checks if usr clicked on page
document.addEventListener("click", function(event) {
    //makes constant variable from ID
    const popup = document.getElementById("popup")
    const accountLink = document.getElementById("accountpopup");

    // if event target(what the user clicked) was not the pop-up or the accountlink, close pop up
    if (!popup.contains(event.target) && event.target !== accountLink){
        CloseAccountmanage();
    }
});
