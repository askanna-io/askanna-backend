from django.core.mail import EmailMultiAlternatives
from django.template import loader


def send_email(
    subject_template_name: str,
    email_template_name: str,
    html_email_template_name: str,
    from_email: str,
    to_email: str,
    context: dict | None = None,
    attachments: list | None = None,
    inline_attachments: list | None = None,
):
    """
    Send email function which loads templates from the filesytem
    """
    context = {} if context is None else context.copy()
    attachments = [] if attachments is None else attachments.copy()
    inline_attachments = [] if inline_attachments is None else inline_attachments.copy()

    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, "text/html")

    for attachment in attachments:
        email_message.attach_file(attachment)

    for attachment in inline_attachments:
        email_message.attach(attachment)

    email_message.mixed_subtype = "related"
    email_message.send()
