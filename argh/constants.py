# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010—2013 Andrey Mikhaylenko and contributors
#
#  This file is part of Argh.
#
#  Argh is free software under terms of the GNU Lesser
#  General Public License version 3 (LGPLv3) as published by the Free
#  Software Foundation. See the file README for copying conditions.
#

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

# forcing argparse.Namespace object instead of signature introspection
ATTR_EXPECTS_NAMESPACE_OBJECT = 'argh_expects_namespace_object'

#-----------------------------------------------------------------------------
#
# deprecated
#
ATTR_INFER_ARGS_FROM_SIGNATURE = 'argh_infer_args_from_signature'
