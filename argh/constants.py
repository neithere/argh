# -*- coding: utf-8 -*-
#
#  Copyright (c) 2010—2012 Andrey Mikhailenko and contributors
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

# explicit command name
ATTR_ALIAS = 'argh_alias'

# declared arguments
ATTR_ARGS = 'argh_args'

# forcing plain signature (instead of an argparse.Namespace object)
ATTR_NO_NAMESPACE = 'argh_no_namespace'

# list of exception classes that should be wrapped and printed as results
ATTR_WRAPPED_EXCEPTIONS = 'argh_wrap_errors'
