'''*****************************************************************
*	Module:			app
*
*	Created:		Dec 4, 2015
*
*	Abstract:		Application utilities.
*
*	Author:			Albert Berger [ alberger@gmail.com ].
*
*****************************************************************'''
__lastedited__ = "2015-12-26 03:51:48"

import sys, os, pwd, signal, threading, re
from configparser import ConfigParser, ExtendedInterpolation
from enum import Enum

APPNAME 			 = None
homedir 			 = None
confdir 			 = None

# Exceptions

errStrings = ["Program error", "Operation successfull", "Unknown data format", "Value doesn't exist",
			"Value already exists",	"Operation failed", "Permission denied", 
			"Name error", "Cannot connect to server",
			"Client connection error", '','','','','','','','','','',"Object doesn't exist", 
			"Unrecognized parameter", "Unrecognized syntax", "Object already exists", 
			"Unsupported parameter value"]

class ErrorCode(Enum):
	'''Error codes for IKException class'''
	programError		 = 0
	success				 = 1
	unknownDataFormat 	 = 2
	valueNotExists		 = 3
	valueAlreadyExists	 = 4
	operationFailed		 = 5
	permissionDenied	 = 6
	nameError			 = 7
	cannotConnectToServer= 8
	clientConnectionError= 9
	# Error codes don't start with '1'
	objectNotExists		 = 20
	unrecognizedParameter= 21
	unrecognizedSyntax	 = 22
	objectAlreadyExists	 = 23
	unsupportedParameterValue = 24
	
class IKException( Exception ):
	'''IK exception.'''
	def __init__( self, code, errCause = None, errMsg = None, moreInfo = None ):
		super( IKException, self ).__init__()
		self.raiser = sys._getframe().f_back.f_code.co_name
		self.code = code
		self.cause = errCause
		if errMsg is None and code.value < len( errStrings ):
			self.msg = errStrings[code.value]
		else:
			self.msg = errMsg
		if moreInfo:
			self.msg += ": " + moreInfo

	def __str__( self, *args, **kwargs ):
		return "Exception {0} in {1}:  {2}: {3}".format( self.code,	self.raiser, self.msg,
														self.cause )
	def __format__( self, *args, **kwargs ):
		return self.__str__( *args, **kwargs )

class SignalHandler:
	'''Object-oriented signal handler.'''
	def __init__( self ):
		self.hmap = {}

	def push( self, sig, h ):
		'''Add a handler to the handler stack.'''
		if sig not in self.hmap:
			self.hmap[sig] = []
			signal.signal( sig, self )
		self.hmap[sig].append( h )

	def pop( self, sig ):
		'''Remove a handler from the handler stack.'''
		if sig not in self.hmap or not self.hmap[sig]:
			raise IKException( ErrorCode.objectNotExists, sig, "No handler found." )
		self.hmap[sig].pop()

	def __call__( self, sig, frame ):
		'''Call a handler.'''
		if sig in self.hmap:
			for i in range( len( self.hmap[sig] ), 0, -1 ):
				self.hmap[sig][i - 1]( sig, frame )

sigHandler = SignalHandler()

# Read-only attribute class


def ROAttr( name, typ ):
	s = '''
class CROAttr({0}):
	def __init__(self, silent=False):
		self.{1} = None
		self.silent = silent

	def __get__( self, instance, owner ):
		return self.{1}[id(instance)]

	def __set__( self, instance, value ):
		if self.{1} is None:
			self.{1} = dict()
		if id(instance) not in self.{1}:
			self.{1}[id(instance)] = value
		else:
			if self.silent:
				return
			raise AttributeError( "Attribute is read-only" )
	
	def __delete__( self, instance ):
		raise AttributeError( "Attribute is read-only" )
'''
	sc = s.format( typ.__class__.__name__, name )
	exec(sc)
	return locals()["CROAttr"]( )		

# Main thread notifier
glSignal = threading.Condition()

# Global 'continue' flag
glCont = True

# Utilities		

def get_home_dir():
	'''Return the home directory name.'''
	if homedir:
		return homedir

	username = pwd.getpwuid( os.getuid() )[0]

	if username:
		return os.path.expanduser( '~' + username )
	else:
		return ":"  # No home directory

def get_conf_dir( create = False ):
	'''Return the name of directory for configuration files.'''
	global confdir, homedir

	if confdir:
		return confdir

	if not homedir:
		homedir = get_home_dir()

	if homedir == ":":
		return None

	confhome = os.getenv( "XDG_CONFIG_HOME", homedir + "/.config" )
	if create:
		os.makedirs( confhome + "/" + APPNAME, mode = 0o777, exist_ok = True )
	return confhome + "/" + APPNAME

def read_conf( cnf, flat=True ):
	'''Read configuration from files in standard locations.
		If 'flat' is True, cnf can be a dictionary. Otherwise
		cnf should be a ConfigParser object.
	'''
	cp = ConfigParser( interpolation = ExtendedInterpolation(), delimiters = '=' )
	cp.optionxform = str
	# First reading system-wide settings
	CONFFILE = "/etc/{0}/{0}.conf".format( APPNAME )
	if os.path.isfile( CONFFILE ):
		cp.read( CONFFILE )

	CONFFILE = confdir + "/{0}.conf".format( APPNAME )
	if os.path.isfile( CONFFILE ):
		cp.read( CONFFILE )

	if flat:
		for sec in cp.sections():
			for nam, val in cp.items( sec ):
				cnf[nam] = val
	else:
		cnf.read_dict( cp )

def clc( s ):
	'''Convert to command line form.'''
	return( s.replace( "_", "-" ) )

def declc( s ):
	'''Convert from command line form.'''
	return( s.replace( "-", "_" ) )

def clp( s ):
	'''Make command line parameter.'''
	return( "--" + s.replace( "_", "-" ) )

def splitArgs( s ):
	'''Split a string with quoted components.'''
	r = '(".+?"(?<!\\\)|\S+?) '
	return [x for x in re.split( r, s ) if x]


