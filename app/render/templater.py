from jinja2 import Template


def render_template(template, **context):
    jinja2_template_string = open("templates/" + template, 'r').read()
    template = Template(jinja2_template_string)
    html_template_string = template.render(context)
    return html_template_string
