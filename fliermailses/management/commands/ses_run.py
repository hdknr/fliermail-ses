from django.utils import translation
from django.conf import settings
import djclick as click
from fliermailses import models
from logging import getLogger
log = getLogger()

translation.activate(settings.LANGUAGE_CODE)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    pass

@main.command()
@click.argument('from_address')
@click.argument('to_address')
@click.argument('subject')
@click.argument('text')
@click.pass_context
def send_text(ctx, from_address, to_address, subject, text):
    '''send simple text'''
    source = models.Source.objects.filter(address=from_address).first()
    source.send_email([to_address], subject, text)


@main.command()
@click.argument('source_id')
@click.argument('to_address', nargs=-1)
@click.argument('subject')
@click.argument('text')
@click.pass_context
def send_message(ctx, source_id, to_address, subject, text):
    '''send message'''
    source = models.Source.objects.filter(id=source_id).first()
    source.create_message(
        subject=subject, body=text, to=to_address).send()
