{% if obj.display %}
.. py:{{ obj.type }}:: {{ obj.name }}

> {%- if obj.annotation is not none %}
>
> {%- endif %}
>
> {%- if obj.value is not none %}
>
> ```{eval-rst}
>
> {%- endif %}
> {%- endif %}
>
>
> {{ obj.docstring|indent(3) }}
> ```
>
> {%- endif %}
>
> {{ obj.docstring|indent(3) }}

{% endif %}
