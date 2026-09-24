// Function that adds an item with a specified quantity to the trolley
function addItemToTrolley(itemId, quantity) {
    // Parse quantity to a base-10 integer
    let parsedQty = parseInt(quantity, 10);

    // Ensure quantity is valid and at least 1; cap at maximum limit of 10 items
    if (isNaN(parsedQty) || parsedQty < 1) {
        alert("Please enter a valid quantity of at least 1.");
        return; // Stop execution to prevent sending invalid or 0 values to the server
    } else if (parsedQty > 10) {
        alert("You cannot order more than 10 of a single item.");
        return; // Stop execution if limit exceeded
    }

    // Send POST request to backend with item ID and validated quantity
    fetch('/add_to_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: parsedQty
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Locate navigation cart total element and update formatted price
            const cartLink = document.getElementById('cart-total-link');
            if (cartLink && data.new_total !== undefined) {
                cartLink.innerText = `🛒 $${data.new_total.toFixed(2)}`;
            }
        } else {
            // Display error message returned from server
            alert(data.message);
        }
    })
    .catch(error => console.error('Error adding to trolley:', error));
}

// Function that removes an item from the trolley
function removeItemFromTrolley(itemId) {
    // Send POST request to remove item from backend trolley
    fetch('/remove_from_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_id: itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update main header cart link with updated price
            const cartLink = document.getElementById('cart-total-link');
            if (cartLink) {
                cartLink.innerText = `🛒 $${data.new_total.toFixed(2)}`;
            }

            // Find closest parent card of targeted remove button and delete node
            const button = document.querySelector(`button[data-item-id="${itemId}"]`);
            if (button) {
                const card = button.closest('.trolley-card');
                if (card) {
                    card.remove();
                }
            }

            // Reload page if zero items remain, or update total spans in cart summary
            if (data.item_count === 0) {
                location.reload();
            } else {
                const summaryTotals = document.querySelectorAll('.trolley-summary span:last-child');
                summaryTotals.forEach(element => {
                    element.innerText = `$${data.new_total.toFixed(2)}`;
                });
            }
        } else {
            // Display error message if removal fails
            alert(data.message);
        }
    })
    .catch(error => console.error('Error removing item:', error));
}