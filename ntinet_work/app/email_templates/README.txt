NTInet Operations Platform Email Templates
===========================================

Location:
    app/email_templates/

Templates:
    port_submitted.html  Sent after a port request is successfully submitted.
    port_foc.html        Used when a Firm Order Commitment is confirmed.
    port_exception.html  Used when an order requires attention.
    port_completed.html  Used when a port completes.
    test_email.txt       Used by the SMTP test function.

Editing templates:
    These files may be edited directly with any text or HTML editor.
    Restart the application after editing to ensure the latest template is used.

Placeholders use Python Template syntax and must keep the ${name} format.

Common placeholders:
    ${nti_reference}
    ${customer_name}
    ${order_id}
    ${status}

Additional placeholders:
    port_foc.html:
        ${foc_date}

    port_exception.html:
        ${exception_message}

    port_completed.html:
        ${completed_date}

The application must supply every placeholder used by a template when rendering it.
Changing the wording and HTML is safe. Adding a new placeholder also requires a
matching change in the Python notification code.
