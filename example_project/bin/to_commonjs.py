#!/usr/bin/python



import sys



fname = sys.argv[1]
in_ = file(fname)
out = file('out', 'w')

out.write('''define(function(require, exports, module){ // define is auto generated
var __contracts = contracts;


  var Undefined, Null, Num, Bool, Str, Odd, Even, Pos, Nat, Neg, Self, Any, None;

Undefined =  __contracts.Undefined;
Null      =  __contracts.Null;
Num       =  __contracts.Num;
Bool      =  __contracts.Bool;
Str       =  __contracts.Str;
Odd       =  __contracts.Odd;
Even      =  __contracts.Even;
Pos       =  __contracts.Pos;
Nat       =  __contracts.Nat;
Neg       =  __contracts.Neg;
Self      =  __contracts.Self;
Any       =  __contracts.Any;
None      =  __contracts.None;





''' + in_.read() + '''

});''')

out.close()







