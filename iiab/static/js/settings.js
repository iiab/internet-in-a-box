$(function() {
    $lang_select = $("select#language_select");

    $.ajax({
        url: languages_url,
        type: "GET",
        dataType: "json",
        success: function(json) {
            // Build options for select box
            $.each( json, function(index, value) {
                $lang_select.append('<option value="'+index+'">'+value+'</option>');
            });

            // Select the user's current language
            $.ajax({
                url: user_language_url,
                type: "GET",
                dataType: "json",
                success: function(json) {
                    console.log("language: ", json.language); 
                },
            });

        },
    });

    // Update user's language when they select a new option
    $lang_select.on("change", function(event) {
        console.log("Event: ", event);
    });
});
