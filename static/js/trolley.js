function addItemToTrolley(item_ID, quantity) {

    fetch('/add_to_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_ID: item_ID,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {

        console.log(data.message);

    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function removeItemFromTrolley(item_ID) {

    fetch('/remove_from_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_ID: item_ID
        })
    })
    .then(response => response.json())
    .then(data => {

        console.log(data.message);

        // Reload trolley after removing
        location.reload();

    })
    .catch(error => {
        console.error('Error:', error);
    });
}