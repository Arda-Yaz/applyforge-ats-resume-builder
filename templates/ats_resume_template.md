# {{ personal.name }}

{{ personal.location }} | {{ personal.email }} | {{ personal.phone }}  
LinkedIn: {{ personal.linkedin }} | GitHub: {{ personal.github }}

## Target

{{ target_title }}

## Summary

{{ summary }}

## Technical Skills

{% for category, skills in skills.items() %}
**{{ category }}:** {{ skills | join(", ") }}
{% endfor %}

## Experience

{% for exp in experience %}
### {{ exp.title }} — {{ exp.company }}
{{ exp.location }} | {{ exp.start }} - {{ exp.end }}

{% for bullet in exp.selected_bullets %}
- {{ bullet.text }}
{% endfor %}
{% endfor %}

## Projects

{% for project in projects %}
### {{ project.name }}
**Tech:** {{ project.tech | join(", ") }}

{% for bullet in project.selected_bullets %}
- {{ bullet.text }}
{% endfor %}
{% endfor %}

## Education

{% for edu in education %}
### {{ edu.degree }} — {{ edu.school }}
{{ edu.location }} | {{ edu.start }} - {{ edu.end }}
{% endfor %}