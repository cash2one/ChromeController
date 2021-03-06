### Chrome Remote Debug Protocol interface layer and toolkit.

Interface for communicating/controlling a remote chrome instance via the Chrome 
Remote Debugger protocol.

Automatic wrapper class creation for the remote interface by parsing
the chrome `protocol.json` file, and dynamic code generation through dynamic 
AST building. While this is not the most maintainable design, I chose it mostly
because I wanted an excuse to learn/experiment with python AST manipulation.

A higher level automation layer is implemented on top of the autogenerated 
wrapper. Both the higher-level interface, and it's associated documentation are 
very much a work in process at the moment.

Interface documentation is here:  
https://fake-name.github.io/ChromeController/ChromeController.CromeRemoteDebugInterface.html

All remote methods are wrapped in named functions, with (partial) validation 
of passed parameter types and return types.
Right now, simple parameter type validation is done (e.g. text arguments must be
of type string, numeric arguments must be either an int or a float, etc..). 
However, the compound type arguments (bascally, anything that takes an array 
or object) are not validated, due to the complexity of properly constructing 
type validators for their semantics given the architecture (read: writing the
validator in raw AST broke my brain).

Tested mostly on python 3.5, lightly on 3.4 and 3.6, all on linux. If you are 
using python 2, please stahp. Will probably work with normal chromium/windows, 
but that's not tested. My  use-case is controlling chromium's `headless_shell`, 
and the system I do testing on has no X install at all, so non-headless testing 
is not something I can do at the moment.

Note that this tool generates and manipulates the AST directly, so it is 
EXTREMELY sensitive to implementation details. It is *probably* broken on 
python > 3.6 or < 3.4.

Transport layer (originally) from https://github.com/minektur/chrome_remote_shell

License:
BSD


------

Current Usage so far has been basically to find bugs or strangeness in the 
chromium remote debug interface:

 - Strange Behaviour is `network.getCookies` (fixed)  
     https://bugs.chromium.org/p/chromium/issues/detail?id=668932
 - `network.clearBrowserCookies` appears to have no effect  
     https://bugs.chromium.org/p/chromium/issues/detail?id=672744

