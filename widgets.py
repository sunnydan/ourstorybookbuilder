from django import forms
from django.utils.safestring import mark_safe
import settings
from recaptcha.client import captcha


class ReCaptcha(forms.widgets.Widget):
    recaptcha_challenge_name = 'recaptcha_challenge_field'
    recaptcha_response_name = 'recaptcha_response_field'

    def render(self, name, value, attrs=None):
        return mark_safe(u'{0}'.format(
                captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY)))

    def value_from_datadict(self, data, files, name):
        return [data.get(self.recaptcha_challenge_name, None),
                data.get(self.recaptcha_response_name, None)]
