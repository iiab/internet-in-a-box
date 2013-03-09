{#
    anchor - css ID of the form field, typical format "#tag"
    completion_url - url at which word list can be fetched
#}
{% macro attach_autocomplete(anchor, completion_url) %}
<script type="text/javascript">
<!--
    $(function(){
        $.getJSON("{{completion_url}}", function(data) {
            $("{{anchor}}").autocomplete({ source: data.completions });
        });
    });
-->
</script>
{% endmacro %}
