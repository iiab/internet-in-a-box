$(function() {
    $lang_select = $("select#language_select");

    $.ajax({
        url: languages_url,
        type: "GET",
        dataType: "json",
        success: function(json) {
            // Build options for select box
            $.each( json, function(index, value) {
                $lang_select.append( $("<option></option>").attr("value", index).text(value) );
            });

            // Select the user's current language
            $.ajax({
                url: user_language_url,
                type: "GET",
                dataType: "json",
                success: function(json) {
                    $lang_select.val(json.language);
                    $lang_select.selectmenu("refresh");
                },
            });

        },
    });

    // Update user's language when they select a new option
    $lang_select.on("change", function(event) {
	$.ajax({
            url: user_language_url,
            type: "PUT",
            dataType: "json",
            data: { language: $(this).val() },
            success: function(json) {
                location.reload();
            },
	});
    });
});
