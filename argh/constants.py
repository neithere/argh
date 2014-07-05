# coding: utf-8
#
#  Copyright © 2010—2014 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README.rst for copying conditions.
#
import argparse

__all__ = (
    'ATTR_NAME', 'ATTR_ALIASES', 'ATTR_ARGS', 'ATTR_WRAPPED_EXCEPTIONS',
    'ATTR_WRAPPED_EXCEPTIONS_PROCESSOR', 'ATTR_EXPECTS_NAMESPACE_OBJECT',
    'PARSER_FORMATTER', 'DEFAULT_ARGUMENT_TEMPLATE'
)


#
# Names of function attributes where Argh stores command behaviour
#

# explicit command name (differing from function name)
ATTR_NAME = 'argh_name'

# alternative command names
ATTR_ALIASES = 'argh_aliases'

# declared arguments
ATTR_ARGS = 'argh_args'

# list of exception classes that should be wrapped and printed as results
ATTR_WRAPPED_EXCEPTIONS = 'argh_wrap_errors'

# a function to preprocess the exception object when it is wrapped
ATTR_WRAPPED_EXCEPTIONS_PROCESSOR = 'argh_wrap_errors_processor'

# forcing argparse.Namespace object instead of signature introspection
ATTR_EXPECTS_NAMESPACE_OBJECT = 'argh_expects_namespace_object'

#
# Other library-wide stuff
#

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


PARSER_FORMATTER = CustomFormatter
"""
Default formatter to be used in implicitly instantiated ArgumentParser.
"""


DEFAULT_ARGUMENT_TEMPLATE = '%(default)s'
"""
Default template of argument help message (see issue #64).
The template ``%(default)s`` is used by `argparse` to display the argument's
default value.
"""

#-----------------------------------------------------------------------------
#
# deprecated
#
ATTR_INFER_ARGS_FROM_SIGNATURE = 'argh_infer_args_from_signature'
