const BASE_URL = "http://127.0.0.1:5000";

$deck = $("#deck-id");

$("li form input").on("click", async function (evt) {
    //evt.preventDefault();

    let card_id = $(this).parent().attr('id');
    let qty = $(this).attr('value');
    let card_name = $(this).attr('name')
    let deck_id = $deck.html();
    let int_deck_id = parseInt(deck_id);
    let int_qty = parseInt(qty);


    let addedToDeck = await axios.post(`${BASE_URL}/decks/${int_deck_id}/add`, {
        card_id,
        int_qty,
        int_deck_id,
        card_name
    });

});