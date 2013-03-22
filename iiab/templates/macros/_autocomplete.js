{#
    anchor - css ID of the form field, typical format "#tag"
    completion_url - url at which word list can be fetched
#}
{% macro attach_autocomplete(anchor, completion_url) %}
<script type="text/javascript">
<!--
    $(function(){
        {% if True %}
        $("{{anchor}}").autocomplete({ source: "{{url_for('gutenberg.autocomplete')}}", sortResults: false });
        {% else %}
        $.getJSON("{{completion_url}}", function(data) {
            $("{{anchor}}").autocomplete({ source: data.completions, sortResults: false });
        });
        {% endif %}
    });
-->
</script>
{% endmacro %}
