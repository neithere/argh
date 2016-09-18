
import re
from collections import OrderedDict

PARAM_RE = re.compile(':param (\S*):\s*(.*)')
TYPE_RE = re.compile(':type (\S*):\s*(.*)')
RETURN_RE = re.compile(':return:\s*(.*)')
RTYPE_RE = re.compile(':rtype:\s*(.*)')


def parse_sphinx_doc(doc):
    """
    Parse sphinx docstring and return a dictionary of attributes. If attributes not found they will not be included.
    e.g. for:

    '''
    This is the description

    :param foo: Describe foo
    :type foo: bool
    :return: bar
    '''

    The dict returned:
    {
        'description': 'This is the description',
        'parameters': OrderedDict([
            ('foo', {'description': 'Describe foo', 'type': 'bool'})
        ]),
        'return': {'description': 'bar'}
    }

    Attributes parsed:
    * param
    * type
    * return
    * rtype


    :param doc: The docstring of a function or method
    :type doc: str
    :return: A nested dict containing the attributes
    :rtype: dict
    """


    lines = doc.expandtabs().splitlines()
    found_attribute = False

    doc_dict = {}

    for line in lines:
        line = line.strip()

        param_m = PARAM_RE.search(line)
        type_m = TYPE_RE.search(line)
        return_m = RETURN_RE.search(line)
        rtype_m = RTYPE_RE.search(line)

        if param_m is not None:
            var, description = param_m.groups()
            description = description.strip()
            if description == '': continue
            parameters = doc_dict.get('arguments', OrderedDict())
            param = parameters.get(var, {})
            param['description'] = description
            parameters[var] = param
            doc_dict['arguments'] = parameters

        elif type_m is not None:
            var, type = type_m.groups()
            type = type.strip()
            if type == '': continue
            parameters = doc_dict.get('arguments', OrderedDict())
            param = parameters.get(var, {})
            param['type'] = type
            parameters[var] = param
            doc_dict['arguments'] = parameters

        elif return_m is not None:
            description = return_m.groups()
            description = description[0].strip()
            if description == '': continue
            return_dict = doc_dict.get('return', {})
            return_dict['description'] = description
            doc_dict['return'] = return_dict

        elif rtype_m is not None:
            type = rtype_m.groups()
            type = type[0].strip()
            if type == '': continue
            return_dict = doc_dict.get('return', {})
            return_dict['type'] = type
            doc_dict['return'] = return_dict

        if (param_m or type_m or return_m or rtype_m) is not None:
            found_attribute = True

        if not found_attribute:
            func_description = doc_dict.get('description', '')
            func_description += line+'\n'
            doc_dict['description'] = func_description

    if 'description' in doc_dict:
        doc_dict['description'] = doc_dict['description'].strip()

    return doc_dict