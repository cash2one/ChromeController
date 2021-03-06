"""
"""
import json
import logging
import ast
import os.path
import astor
import sys
import pprint

import os.path


CHECKS = {
	"array"   : ast.Tuple(ctx=ast.Load(), elts=[ast.Name(id='list', ctx=ast.Load()), ast.Name(id='tuple', ctx=ast.Load())]),   # "(list, tuple)",
	"boolean" : ast.Tuple(ctx=ast.Load(), elts=[ast.Name(id='bool', ctx=ast.Load())]),   # "(bool, )",
	"integer" : ast.Tuple(ctx=ast.Load(), elts=[ast.Name(id='int', ctx=ast.Load())]),   # "(int, )",
	"number"  : ast.Tuple(ctx=ast.Load(), elts=[ast.Name(id='float', ctx=ast.Load()), ast.Name(id='int', ctx=ast.Load())]),   # "(float, int)",
	"string"  : ast.Tuple(ctx=ast.Load(), elts=[ast.Name(id='str', ctx=ast.Load())]),   # "(str, )",
}



class JsonInterfaceGenerator(object):
	"""

	"""

	def __init__(self, protocol_major=1, protocol_minor=2, debug_prints=False, *args, **kwargs):
		""" init """

		super().__init__(*args, **kwargs)

		self.line_num = 0
		protocol_major = str(protocol_major)
		protocol_minor = str(protocol_minor)

		self.do_debug_prints = debug_prints

		self.types = {}
		self.protocol = self.__load_protocol(protocol_major, protocol_minor)

		self.__build_interface_class()

	def __load_json_file(self, fname):

		folder = os.path.split(__file__)[0]
		protocol_file_path = os.path.join(folder, "../", 'protocols', fname)
		protocol_file_path = os.path.abspath(protocol_file_path)
		assert(os.path.exists(protocol_file_path)), "Protocol file '{}' appears to be missing!".format(protocol_file_path)

		with open(protocol_file_path) as fp:
			protocol_str = fp.read()
		return json.loads(protocol_str)


	def __load_protocol(self, major, minor):

		protocol_rev = "{}.{}".format(major, minor)
		main_json_file = "browser_protocol-r{}.json".format(protocol_rev)
		js_json_file = "js_protocol-r{}.json".format(protocol_rev)

		js_file_1 = self.__load_json_file(main_json_file)
		js_file_2 = self.__load_json_file(js_json_file)

		self.__validate_protocol_version(main_json_file, js_file_1, major, minor)
		self.__validate_protocol_version(js_json_file, js_file_2, major, minor)

		# assemble the two json files into the single command descriptor file.
		for domain in js_file_2['domains']:
			js_file_1['domains'].append(domain)

		return js_file_1

	def __get_line(self):
		self.line_num += 1
		return self.line_num


	def __validate_protocol_version(self, filename, js_file, major, minor):
		errm_1 = "Major version mismatch: {} - {} in file {}".format(js_file['version']["major"], major, filename)
		errm_2 = "Minor version mismatch: {} - {} in file {}".format(js_file['version']["minor"], minor, filename)

		v_1 = js_file['version']["major"]
		v_2 = js_file['version']["minor"]

		assert isinstance(major, str)
		assert isinstance(minor, str)

		assert v_1 == major, errm_1
		assert v_2 == minor, errm_2


	def __build_interface_class(self):
		# body = ast.
		body = [
			ast.Expr(value=ast.Str(s='\n\n\t')),
			self.__build__init()
		]
		for subdom in self.protocol['domains']:
			subdom_funcs = self.__build_domain_interface(subdom)
			body += subdom_funcs

		# print(body)

		self.interface_class = ast.ClassDef(
				name           = "ChromeRemoteDebugInterface",
				bases          = [ast.Name(id="ChromeInterface", ctx=ast.Load())],
				body           = body,
				keywords       = [],
				decorator_list = [],
				starargs       = None,
				kwargs         = None,
				lineno         = self.__get_line(),
				col_offset     = 0,
				)

		# code = astor.dump_tree(self.interface_class)
		# print(code)

	def __build__init(self):

		super_func = ast.Call(func=ast.Name(id='super', ctx=ast.Load()), args=[], keywords=[])
		if (sys.version_info[0], sys.version_info[1]) == (3, 5) or \
			(sys.version_info[0], sys.version_info[1]) == (3, 6):
			super_func = ast.Call(
									func=ast.Attribute(value=super_func, attr='__init__', ctx=ast.Load()),
									args=[ast.Starred(value=ast.Name(id='args', ctx=ast.Load()), ctx=ast.Load())],
									keywords=[],
									kwargs=ast.Name(id='kwargs', ctx=ast.Load()),
							)
		elif (sys.version_info[0], sys.version_info[1]) == (3,4):
			super_func = ast.Call(
									func=ast.Attribute(value=super_func, attr='__init__', ctx=ast.Load()),
									args=[],
									keywords=[],
									starargs=ast.Name(id='args', ctx=ast.Load()),
									kwargs=ast.Name(id='kwargs', ctx=ast.Load()),
							)
		else:
			print("Version:", sys.version_info)
			raise RuntimeError("This script only functions on python 3.4, 3.5 or 3.6. Active python version {}.{}".format(*sys.version_info))

		super_init = ast.Expr(
							value=super_func,
							lineno     = self.__get_line(),
							col_offset = 0,
						)

		body = [super_init]

		sig = ast.arguments(
					args=[ast.arg('self', None)],
					vararg=ast.arg(arg='args', annotation=None),
					kwarg=ast.arg(arg='kwargs', annotation=None),
					varargannotation=None,
					kwonlyargs=[],
					kwargannotation=None,
					defaults=[],
					kw_defaults=[])

		func = ast.FunctionDef(
			name = "__init__",
			args = sig,
			body = body,
			decorator_list = [],
			lineno     = self.__get_line(),
			col_offset = 0,
			)

		return func

	def __build_domain_interface(self, subdom):
		assert "domain" in subdom

		dom_desc  = subdom.get("descripton", "")
		dom_name  = subdom['domain']
		full_name = subdom['domain']

		for typen in subdom.get('types', []):
			typestr = "{}_{}".format(dom_name, typen['id'])
			assert typen['id'] not in self.types, "Duplicate type name: {}".format(typen['id'])
			self.types[typestr] = typen

		functions = []
		for command in subdom.get('commands', []):
			func = self.__build_function(dom_name, full_name, command)
			functions.append(func)

		return functions

	def __build_desc_string(self, dom_name, func_name, func_params):
		desc = []
		fname = "{}.{}".format(dom_name, func_name)
		desc.append("Function path: {}".format(fname))
		desc.append("	Domain: {}".format(dom_name))
		desc.append("	Method name: {}".format(func_name))
		desc.append("")
		if 'experimental' in func_params and func_params['experimental']:
			desc.append("	WARNING: This function is marked 'Experimental'!")
			desc.append("")


		if "parameters" in func_params:
			desc.append("	Parameters:")
			required = [param for param in func_params['parameters'] if not param.get("optional", False)]
			optional = [param for param in func_params['parameters'] if param.get("optional", False)]
			sections = [
				("		Required arguments:", required),
				("		Optional arguments:", optional),
			]
			sections = [section for section in sections if section[1]]
			for segment_name, items in sections:
				desc.append(segment_name)
				for param in items:
					if not "description" in param:
						param['description'] = "No description"
					if "type" in param:
						desc.append("			\'{}\' (type: {}) -> {}".format(param['name'], param['type'], param['description']))
					else:
						desc.append("			\'{}\' (type: {}) -> {}".format(param['name'], param['$ref'], param['description']))

		if "returns" in func_params:
			desc.append("	Returns:")
			for param in func_params['returns']:
				if not "description" in param:
					param['description'] = "No description"
				if "type" in param:
					desc.append("		\'{}\' (type: {}) -> {}".format(param['name'], param['type'], param['description']))
				else:
					desc.append("		\'{}\' (type: {}) -> {}".format(param['name'], param['$ref'], param['description']))
		else:
			desc.append("	No return value.")

		desc.append("")

		if "description" in func_params:
			desc.append("	Description: {}".format(func_params['description']))

		desc = ["\t\t"+line for line in desc]
		ret = "\n".join(desc)

		return ret

	def __build_conditional_arg_check(self, argname, argtype):

		target_value = ast.Subscript(
							value=ast.Name(id='kwargs', ctx=ast.Load()),
							slice=ast.Index(ast.Str(s=argname)),
							ctx=ast.Load()
							)

		presence_check = ast.Call(func = ast.Name(id='isinstance', ctx=ast.Load()),
				args         = [target_value, argtype],
				keywords     = [],
				lineno       = self.__get_line())

		# Assumes that argtype is a ast.Tuple of ast.Name items
		types = [t.id for t in argtype.elts]

		check_message = ast.BinOp(
				left         = ast.Str(s='Argument {} must be of type ({}). Received type: %s'.format(argname, types)),
				op           = ast.Mod(),
				right        = ast.Call(func=ast.Name(id='type', ctx=ast.Load()), args=[target_value], keywords=[]),
				lineno       = self.__get_line())

		assert_check = ast.Assert(
			test         = presence_check,
			msg          = check_message,
			lineno       = self.__get_line())

		check_body = [assert_check]

		check = ast.Compare(left=ast.Str(s=argname, ctx=ast.Load()), ops=[ast.In()], comparators=[ast.Name(id='kwargs', ctx=ast.Load())])

		new_ret = ast.If(
			test   = check,
			body   = check_body,
			orelse = [],
			lineno = self.__get_line())

		return new_ret

	def __build_unconditional_arg_check(self, argname, argtype):
		# checker_str = "assert isinstance({argname}, {typetuple}), \"Argument {argname} must be of type {typetuple}. Received type: %s\" % type({argname})".format(
		# 		argname = argname,
		# 		typetuple = argtype,
		# 	)
		# checker = ast.parse(checker_str)
		# old_ret = checker.body.pop()

		presence_check = ast.Call(func = ast.Name(id='isinstance', ctx=ast.Load()),
				args         = [ast.Name(id=argname, ctx=ast.Load()), argtype],
				keywords     = [],
				lineno       = self.__get_line())

		check_message = ast.BinOp(
				left         = ast.Str(s='Argument {} must be of type ({}). Received type: %s'.format(argname, argtype)),
				op           = ast.Mod(),
				right        = ast.Call(func=ast.Name(id='type', ctx=ast.Load()), args=[ast.Name(id=argname, ctx=ast.Load())], keywords=[]),
				lineno       = self.__get_line())

		new_ret = ast.Assert(
			test         = presence_check,
			msg          = check_message,
			lineno       = self.__get_line())


		return new_ret

	def __build_debug_print(self, prefix_str, var_name):
		pstmt = ast.Expr(
			value=ast.Call(
				func     = ast.Name(id='print', ctx=ast.Load()),
				args     = [ast.Str(s=prefix_str), ast.Name(id=var_name, ctx=ast.Load())],
				keywords = [],
				lineno   = self.__get_line()
			)
		)
		return pstmt

	def __build_function(self, dom_name, full_name, func_params):

		assert 'name' in func_params
		func_name = func_params['name']

		docstr = self.__build_desc_string(dom_name, func_name, func_params)

		args = [ast.arg('self', None)]
		message_params = []
		func_body = []

		if docstr:
			func_body.append(ast.Expr(ast.Str("\n"+docstr+"\n\t\t")))

		for param in func_params.get("parameters", []):

			argname = param['name']


			param_optional = param.get("optional", False)

			if param_optional is False:
				message_params.append(ast.keyword(argname, ast.Name(id=argname, ctx=ast.Load())))
				args.append(ast.arg(argname, None))
				if self.do_debug_prints:
					func_body.append(self.__build_debug_print(argname, argname))



			param_type = param.get("type", None)
			if param_type in CHECKS:
				if param_optional:
					check = self.__build_conditional_arg_check(argname, CHECKS[param_type])
				else:
					check = self.__build_unconditional_arg_check(argname, CHECKS[param_type])

				if check:
					func_body.append(check)




		optional_params = [param.get("name") for param in func_params.get("parameters", []) if param.get("optional", False)]
		func_kwargs = None
		if len(optional_params):


			value = ast.List(elts=[ast.Str(s=param, ctx=ast.Store()) for param in optional_params], ctx=ast.Load())
			create_list = ast.Assign(targets=[ast.Name(id='expected', ctx=ast.Store())], value=value)

			func_body.append(create_list)

			passed_arg_list = ast.Assign(targets=[ast.Name(id='passed_keys', ctx=ast.Store())],
				value=ast.Call(func=ast.Name(id='list', ctx=ast.Load()),
				args=[ast.Call(func=ast.Attribute(value=ast.Name(id='kwargs', ctx=ast.Load()), attr='keys', ctx=ast.Load()), args=[], keywords=[])],
				keywords=[]))

			func_body.append(passed_arg_list)

			comprehension = ast.comprehension(target=ast.Name(id='key', ctx=ast.Store()), iter=ast.Name(id='passed_keys', ctx=ast.Load()), ifs=[], is_async=False)
			comparator = ast.Name(id='expected', ctx=ast.Load())

			listcomp = ast.ListComp(elt=ast.Compare(left=ast.Name(id='key', ctx=ast.Load()), ops=[ast.In()], comparators=[comparator]), generators=[comprehension])

			check_message = ast.BinOp(
					left         = ast.Str(s="Allowed kwargs are {}. Passed kwargs: %s".format(optional_params)),
					op           = ast.Mod(),
					right        = ast.Name(id='passed_keys', ctx=ast.Load()),
					lineno       = self.__get_line())

			kwarg_check = ast.Assert(test=ast.Call(func=ast.Name(id='all', ctx=ast.Load()), args=[listcomp], keywords=[]), msg=check_message)
			func_body.append(kwarg_check)

			func_kwargs = ast.Name(id='kwargs', ctx=ast.Load())


		fname = "{}.{}".format(dom_name, func_name)
		fname = ast.Str(s=fname, ctx=ast.Load())


		if (sys.version_info[0], sys.version_info[1]) == (3, 5) or \
			(sys.version_info[0], sys.version_info[1]) == (3, 6):

			# More irritating minor semantic differences in the AST between 3.4 and 3.5
			if func_kwargs:
				message_params.append(ast.keyword(arg=None, value=ast.Name(id='kwargs', ctx=ast.Load())))

			communicate_call = ast.Call(
					func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), ctx=ast.Load(), attr='synchronous_command'),
					args=[fname],
					keywords=message_params)

		elif (sys.version_info[0], sys.version_info[1]) == (3,4):

			communicate_call = ast.Call(
					func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), ctx=ast.Load(), attr='synchronous_command'),
					args=[fname],
					kwargs=func_kwargs,
					keywords=message_params)
		else:
			print("Version:", sys.version_info)
			raise RuntimeError("This script only functions on python 3.4, 3.5 or 3.6. Active python version {}.{}".format(*sys.version_info))


		do_communicate = ast.Assign(targets=[ast.Name(id='subdom_funcs', ctx=ast.Store())], value=communicate_call)
		func_ret = ast.Return(value=ast.Name(id='subdom_funcs', ctx=ast.Load()))


		if len(optional_params) and self.do_debug_prints:
			func_body.append(self.__build_debug_print('kwargs', 'kwargs'))

		func_body.append(do_communicate)
		func_body.append(func_ret)

		if len(optional_params):
			kwarg = ast.arg(arg='kwargs', annotation=None)
		else:
			kwarg = None


		sig = ast.arguments(
					args=args,
					vararg=None,
					varargannotation=None,
					kwonlyargs=[],
					kwarg=kwarg,
					kwargannotation=None,
					defaults=[],
					kw_defaults=[])

		func = ast.FunctionDef(
			name = "{}_{}".format(full_name, func_name),
			args = sig,
			body = func_body,
			decorator_list = [],
			lineno     = self.__get_line(),
			col_offset = 0,
			)

		return func

	def __to_module(self):

		module_components = [
			ast.ImportFrom(module="ChromeController.transport",    names=[ast.alias('ChromeSocketManager', None)], level=0),
			ast.ImportFrom(module="ChromeController.manager_base", names=[ast.alias('ChromeInterface',     None)], level=0),
			self.interface_class,
		]

		mod = ast.Module(module_components, lineno=self.__get_line(), col_offset=1)

		mod = ast.fix_missing_locations(mod)

		return mod

	def dump_class(self):
		indent = "	"
		return astor.to_source(self.__to_module(), indent_with=indent)

	def dump_ast(self):
		return astor.dump_tree(self.__to_module())

	def compile_class(self):
		mod = self.__to_module()
		code = compile(self.__to_module(), "no filename", "exec")
		exec(code)
		built_class = locals()['ChromeRemoteDebugInterface']

		return built_class

def get_source():
	instance = JsonInterfaceGenerator()
	return instance.dump_class()

def get_class_def():
	instance = JsonInterfaceGenerator()
	ret = instance.compile_class()
	return ret

def get_printed_ast():
	instance = JsonInterfaceGenerator()
	return instance.dump_ast()



def print_file_ast():
	with open(__file__) as fp:
		this_source = fp.read()
	this_ast = ast.parse(this_source)

	print("AST:")
	print("astor.dump_tree(this_ast)")
	print(astor.dump_tree(this_ast))

def update_generated_class():
	log = logging.getLogger("Main.ChromeController.WrapperGenerator")
	gen_filename = "Generated.py"
	cur_file = os.path.abspath(__file__)
	cur_dir  = os.path.dirname(cur_file)

	fname = os.path.join(cur_dir, gen_filename)

	cls_def = get_source()
	try:
		with open(fname, "r", encoding='utf-8') as fp:
			have = fp.read()
	except IOError:
		# The class hasn't been generated yet?
		have = ""

	if have.strip() != cls_def.strip():
		log.info("ChromeController wrapper is up to date. Nothing to do")
	else:
		log.warning("Generated wrapper appears to be out of date. Regenerating.")
		log.warning("Note: If ChromeController is installed as a module, "
		                 "this may require administrator permissions")
		try:
			with open(fname, "w", encoding='utf-8') as fp:
				fp.write(cls_def)
		except IOError:
			raise IOError("Could not update class definition file: {}, and "
			              "it is out of date!".format(fname))


def test():
	print(JsonInterfaceGenerator)
	# print_file_ast()
	instance = JsonInterfaceGenerator()
	print("ast:")
	print(instance.dump_ast())
	newsauce = instance.dump_class()
	print("Class:")
	print(newsauce)
	print(instance.compile_class())
	# print(instance)

if __name__ == '__main__':
	test()
	print_file_ast()



