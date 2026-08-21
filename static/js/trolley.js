function addItemToTrolley(itemId, quantity) {
    fetch('/add_to_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_ID: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the text on the page in real-time
            const cartLink = document.getElementById('cart-total-link');
            if (cartLink && data.new_total !== undefined) {
                cartLink.innerText = `🛒 $${data.new_total.toFixed(2)}`;
            }
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error adding to trolley:', error));
}


function removeItemFromTrolley(itemId) {
    fetch('/remove_from_trolley', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            item_ID: itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 1. Update the header cart link
            const cartLink = document.getElementById('cart-total-link');
            if (cartLink) {
                cartLink.innerText = `🛒 $${data.new_total.toFixed(2)}`;
            }

            // 2. Remove the item card from the page
            const button = document.querySelector(`button[data-item-id="${itemId}"]`);
            if (button) {
                const card = button.closest('.trolley-card');
                if (card) {
                    card.remove();
                }
            }

            // 3. If no items remain, reload to show the "empty cart" state
            if (data.item_count === 0) {
                location.reload();
            } else {
                // Otherwise, update the summary card totals on the trolley page
                const summaryTotals = document.querySelectorAll('.trolley-summary span:last-child');
                summaryTotals.forEach(element => {
                    element.innerText = `$${data.new_total.toFixed(2)}`;
                });
            }
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error removing item:', error));
}