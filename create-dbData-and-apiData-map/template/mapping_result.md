# DB fields and API data fields Mapping Result

{% set before_db_table = '' %}
{% set before_db_field = '' %}
{% set before_base_name = '' %}
{% set before_base_field = '' %}
{% set before_api_name = '' %}

|#|DB<br> Table|DB<br> Field|DB Base<br> Record|DB Base<br> Field|API Path|API Field<br> Name|API Field<br> Type|API Field<br>(Max Value)|API Field<br>(Min Value)|API Field<br>(Max length)|API Field<br>(Min length)|
|:--|:--|:--|:--|:--|:--|:--|--:|--:|--:|--:|
{% for data in mapping_result_list %}
|{{ loop.index }}|{% if before_db_table == data.db_table %} {% else %}{{ data.db_table }}{% set before_db_table = data.db_table %}{% endif %}|{% if before_db_field == data.db_field %} {% else %}{{ data.db_field }}{% set before_db_field = data.db_field %}{% endif %}|{% if before_base_name == data.base_name %} {% else %}{{ data.base_name }}{% set before_base_name = data.base_name %}{% endif %}|{% if before_base_field == data.base_field %} {% else %}{{ data.base_field }}{% set before_base_field = data.base_field %}{% endif %}|{% if before_api_name == data.api_name %} {% else %}{{ data.api_name }}{% set before_api_name = data.api_name %}{% endif %}|{{ data.api_field_name }}|{{ data.api_field_type }}|{{ data.api_field_max_value }}|{{ data.api_field_min_value }}|{{ data.api_field_max_len }}|{{ data.api_field_min_len }}|
{% endfor %}