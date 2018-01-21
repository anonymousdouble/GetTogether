from django.utils.safestring import mark_safe
from django.forms import ModelForm, Field, SplitDateTimeWidget, DateInput, MultiWidget, Select
from django.forms.widgets import TextInput, Media
from django.utils.translation import ugettext_lazy as _

from .models.profiles import Team
from .models.events import Event, Place

from datetime import time
from time import strptime, strftime

class LookupMedia(Media):
    def render(self):
        return mark_safe('''<script type="text/javascript"><script>
$(document).ready(function(){
    $("#{{ widget.name }}_search").keyup(function() {
	var searchText = this.value;
	$.getJSON("{{ widget.source }}?q="+searchText, function(data) {
	    var selectField = $("#{{ widget.name }}_select");
	    selectField.empty();
	    $.each(data, function(){
		selectField.append('<option value="'+ this.{{ widget.key }} +'">'+ this.{{ widget.label }} + '</option>')
	    });
	});
    });
});
</script>''')

class Lookup(TextInput):
    input_type = 'text'
    template_name = 'forms/widgets/lookup.html'
    add_id_index = False
    checked_attribute = {'selected': True}
    option_inherits_attrs = False

    def __init__(self, source='#', key="id", label="name", attrs=None):
        super().__init__(attrs)
        self.source = source
        self.key = key
        self.label = label
        self.name = 'place'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['source'] = self.source
        context['widget']['key'] = self.key
        context['widget']['label'] = self.label
        return context

class DateWidget(DateInput):
    """A more-friendly date widget with a pop-up calendar.
    """
    template_name = 'forms/widgets/date.html'
    def __init__(self, attrs=None):
        self.date_class = 'datepicker'
        if not attrs:
            attrs = {}
        if 'date_class' in attrs:
            self.date_class = attrs.pop('date_class')
        if 'class' not in attrs:
            attrs['class'] = 'date'

        super(DateWidget, self).__init__(attrs=attrs)


class TimeWidget(MultiWidget):
    """A more-friendly time widget.
    """
    def __init__(self, attrs=None):
        self.time_class = 'timepicker'
        if not attrs:
            attrs = {}
        if 'time_class' in attrs:
            self.time_class = attrs.pop('time_class')
        if 'class' not in attrs:
            attrs['class'] = 'time'

        widgets = (
            Select(attrs=attrs, choices=[(i + 1, "%02d" % (i + 1)) for i in range(0, 12)]),
            Select(attrs=attrs, choices=[(i, "%02d" % i) for i in range(00, 60, 15)]),
            Select(attrs=attrs, choices=[('AM', _('AM')), ('PM', _('PM'))])
        )

        super(TimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, str):
            try:
                value = strptime(value, '%I:%M %p')
            except:
                value = strptime(value, '%H:%M:%S')
            hour = int(value.tm_hour)
            minute = int(value.tm_min)
            if hour < 12:
                meridian = 'AM'
            else:
                meridian = 'PM'
                hour -= 12
            return (hour, minute, meridian)
        elif isinstance(value, time):
            hour = int(value.strftime("%I"))
            minute = int(value.strftime("%M"))
            meridian = value.strftime("%p")
            return (hour, minute, meridian)
        return (None, None, None)

    def value_from_datadict(self, data, files, name):
        value = super(TimeWidget, self).value_from_datadict(data, files, name)
        t = strptime("%02d:%02d %s" % (int(value[0]), int(value[1]), value[2]), "%I:%M %p")
        return strftime("%H:%M:%S", t)

    def format_output(self, rendered_widgets):
        return '<span class="%s">%s%s%s</span>' % (
            self.time_class,
            rendered_widgets[0], rendered_widgets[1], rendered_widgets[2]
        )

class DateTimeWidget(SplitDateTimeWidget):
    """
    A more-friendly date/time widget.
    """
    def __init__(self, attrs=None, date_format=None, time_format=None):
        super(DateTimeWidget, self).__init__(attrs, date_format, time_format)
        self.widgets = (
            DateWidget(attrs=attrs),
            TimeWidget(attrs=attrs),
        )

    def decompress(self, value):
        if value:
            d = strftime("%Y-%m-%d", value.timetuple())
            t = strftime("%I:%M %p", value.timetuple())
            return (d, t)
        else:
            return (None, None)

    def format_output(self, rendered_widgets):
        return '%s %s' % (rendered_widgets[0], rendered_widgets[1])

    def value_from_datadict(self, data, files, name):
        values = super(DateTimeWidget, self).value_from_datadict(data, files, name)
        return ' '.join(values)

class TeamForm(ModelForm):
    class Meta:
        model = Team
        fields = '__all__'

class NewTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'country', 'spr', 'city', 'web_url', 'tz']
        widgets = {
            'country': Lookup(source='/api/country/', label='name'),
            'spr': Lookup(source='/api/spr/', label='name'),
            'city': Lookup(source='/api/cities/', label='name'),
        }
        raw_id_fields = ('country','spr','city')

class TeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place', 'web_url', 'announce_url', 'tags']
        widgets = {
            'country': Lookup(source='/api/country/', label='name'),
            'spr': Lookup(source='/api/spr/', label='name'),
            'city': Lookup(source='/api/cities/', label='name'),
        }

class NewTeamEventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'start_time', 'end_time', 'summary', 'place']
        widgets = {
            'place': Lookup(source='/api/places/', label='name'),
            'start_time': DateTimeWidget,
            'end_time': DateTimeWidget
        }

class NewPlaceForm(ModelForm):
    class Meta:
        model = Place
        fields = ['name', 'address', 'city', 'longitude', 'latitude', 'place_url', 'tz']
        widgets = {
            'city': Lookup(source='/api/cities/', label='name'),
        }
