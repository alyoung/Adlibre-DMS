"""

"""
from django import forms
from plugins.models import Plugin, PluginPoint
from django.utils.importlib import import_module
from .models import DoccodePluginMapping

def create_form_fields(plugins_param = ''):
    """
    Generator of form fields in desired grouping.
    
    Takes Plugin model queryset or produces own from all plugins.
    
    Makes:
    - getting all plugins queryset if not given
    - getting used plugins types and cleaning them to disable repeating of them
    - grouping fields for PluginSelectorForm 
    
    Returns kwargs dictionary with form fields to populate form.
    """
    # getting all plugins queryset if not given
    if plugins_param == '':
        plugins = Plugin.objects.all()
    else:
        plugins = plugins_param
    # init
    all_plugins_types = []
    plugin_types_clean = []
    plugins_done = []
    kwargs = {}
    # getting used plugins types and cleaning them to disable repeating of them
    for plugin in plugins:
        plugin_temp = plugin.get_plugin()
        plugin_temp.pk = plugin.pk
        plugins_done.append(plugin_temp)
        all_plugins_types.append(plugin_temp.plugin_type)
        # appending all unique types to types list
        if not (plugin_temp.plugin_type in plugin_types_clean):
            plugin_types_clean.append(plugin_temp.plugin_type)
    
    # grouping fields for PluginSelectorForm
    for plugin_type in plugin_types_clean:
        plugins_temp_list = []
        for plugin in plugins_done:
            if plugin.plugin_type == plugin_type:
                #add plugin to current plugins list
                plugins_temp_list.append(plugin.pk)
        #saving plugins list to main dict
        kwargs[plugin_type] = forms.ModelMultipleChoiceField(plugins.filter(pk__in = plugins_temp_list))
    return kwargs

def get_all_plugintypes(plugins_param = ''):
    """
    Helper function to get list of unique plugin types
    
    Takes Plugin model queryset or peoduces own from 1 request if not provided.
    Returns list of cleared and unique plugins types used.
    """
    # init
    if plugins_param == '':
        plugins = Plugin.objects.all()
    else:
        plugins = plugins_param
    plugins_types_clean = []

    for plugin in plugins:
        plugin_temp = plugin.get_plugin()
        # appending all unique types to types list
        if not (plugin_temp.plugin_type in plugins_types_clean):
            plugins_types_clean.append(plugin_temp.plugin_type)
    return plugins_types_clean

def extract_plugin_pks(input_post_data, plugins_queryset = False):
    """
    Reduces form POST data to list of submitted plugin's PK's.
    
    Returns list of POST form plugin's PK's.
    Takes:
    - serialized form POST data
    - Plugin model queryset, or produces own if not provided.
    """
    if not plugins_queryset: plugins_queryset = Plugin.objects.all()
    clean_plugintypes = get_all_plugintypes(plugins_queryset)
    requested_plugin_pks = []
    # clean form POST and list all plugin's PK's
    for form_field_name in input_post_data:
        if form_field_name in clean_plugintypes:
            #field is Plugin's type field
            requested_plugin_pks.extend(input_post_data.getlist(form_field_name))
    return requested_plugin_pks
    
    
def sort_plugins_by_pluginpoint(requested_plugin_pks, plugins_queryset = False):
    """
    Creates a dictionary of plugin PK's sorted by pluginpont.
    Suitable for model manipulations.
    
    Ruturns a dictionary of key:pluginpoint name, value: list of submited plugin PK's
    Takes:
    - list of submitted plugin's PK's (cleared to only numbers) 
    - plugins model queryset or produces one for own usage.
    """
    plugins_sorted_dict = {}
    if not plugins_queryset: plugins_queryset = Plugin.objects.all()
    for plugin_pk in requested_plugin_pks:
        current_plugin = plugins_queryset.filter(pk=plugin_pk)
        plugin_instance = current_plugin[0].get_plugin()
        # if plugins of this point were NOT added before create this KEY
        if not plugins_sorted_dict.has_key(plugin_instance.settings_field_name):
            plugins_sorted_dict[plugin_instance.settings_field_name] = []
        # add a plugin to selected pluginpoint list
        plugins_sorted_dict[plugin_instance.settings_field_name].append(plugin_pk)
    return plugins_sorted_dict

def save_doccode_model(plugins_sorted_dict, input_post_data):
    """
    Model instance aving sequence.
    Takes 2 arguments: 
    - dictionary of properly sorted plugins pk's 
    - serialized input POST string
    creates a model instance and saves to base.
    Needs ONLY validated data. 
    """
    mapping = DoccodePluginMapping()
    mapping.active = input_post_data.has_key('active')
    mapping.doccode = input_post_data['doccode']
    mapping.save()
    for field_name, value in plugins_sorted_dict.iteritems():
        setattr(mapping, field_name, value)
    mapping.save()
    return mapping


def get_all_pluginpoints_dict(all_pluginpoints_queryset = False):
    """
    Returns dictionary pluginpoint.pk : pluginpoint.settings_field_name
    For e.g.:
    '4' : 'before_removal_plugins',
    
    Takes pluginpoints queryset or makes call to base on his own, 
    using all pluginpoits there, if not provided.
    """
    if not all_pluginpoints_queryset:
        all_pluginpoints_queryset = PluginPoint.objects.all()
    pluginpoints_dict = {}
    for point in all_pluginpoints_queryset:
        pluginpoint = get_plugin_from_string(point.name)
        pluginpoints_dict[str(point.pk)] = pluginpoint.settings_field_name
    return pluginpoints_dict


def get_plugin_from_string(plugin_name):
    """
    Returns plugin or plugin point class from given ``plugin_name`` string.

    Example of ``plugin_name``::
        'my_app.MyPlugin'
    """
    modulename, classname = plugin_name.rsplit('.', 1)
    module = import_module(modulename)
    return getattr(module, classname)

def save_PluginSelectorForm(serialized_POST, plugins_queryset = False):
    """
    Main form save sequence manager.
    Uses methods above to save model instance based on provided form data.
    """
    if not plugins_queryset: plugins_queryset = Plugin.objects.all()
    plugins_used_list = extract_plugin_pks(serialized_POST, plugins_queryset)
    plugins_sorted_dict = sort_plugins_by_pluginpoint(plugins_used_list, plugins_queryset)
    instance_ = save_doccode_model(plugins_sorted_dict, serialized_POST)
    return instance_