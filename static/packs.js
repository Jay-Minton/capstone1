const BASE_URL = "http://127.0.0.1:5000";

$deck = $("#deck-id");

$("li form input").on("click", async function (evt) {
    evt.preventDefault();

    let pack_code= $(this).parent().attr('id');
    let pack_name = $(this).parent().attr('name');
    console.log(pack_name, pack_code);
    if(this.value == "add") {
        this.value = "remove";
        $(this).addClass("pack-clicked");
    }
    else {
        this.value = "add";
        $(this).removeClass("pack-clicked");
    }

    let addedToCollection = await axios.post(`${BASE_URL}/collection/add`, {
        pack_code,
        pack_name
    });

});